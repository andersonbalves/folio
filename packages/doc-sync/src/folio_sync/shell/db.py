"""Database initialization and connection management for the standalone SQLite architecture."""

from __future__ import annotations

import json
import sqlite3
import struct
from collections.abc import Generator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING

import sqlite_vec
import structlog
from folio_core.splitter import split_document

from folio_sync.core.indexer import prepare_document

if TYPE_CHECKING:
    from folio_embeddings import Embedder

logger = structlog.get_logger()


def init_db(db_path: Path, embedder: Embedder | None = None) -> None:
    """Inicializa o schema do SQLite."""
    logger.info("db.init", path=str(db_path))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect_db(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                path TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                content_hash TEXT,
                metadata TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                slug TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                category TEXT,
                doc_path TEXT,
                sort_order INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_topics_category ON topics (category, sort_order)"
        )
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                path UNINDEXED,
                title,
                content,
                tokenize='trigram'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY,
                doc_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                heading_path TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_path) REFERENCES documents(path) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                chunk_id UNINDEXED,
                doc_path UNINDEXED,
                heading_path UNINDEXED,
                content,
                tokenize='trigram'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        if embedder is not None and embedder.dimensions > 0:
            query = f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings USING vec0(
                    chunk_id INTEGER PRIMARY KEY,
                    embedding float[{int(embedder.dimensions)}]
                )
            """  # nosec B608
            conn.execute(query)  # nosemgrep
        conn.commit()


@contextmanager
def connect_db(db_path: Path) -> Generator[sqlite3.Connection]:
    """Conecta ao banco e carrega a extensão sqlite-vec."""
    conn = sqlite3.connect(db_path)
    try:
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.close()


class SQLiteDocumentRepository:
    """Deep SQLite repository adapter for documents."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        embedder: Embedder | None = None,
        chunk_size: int = 512,
        chunk_max_size: int = 1024,
    ):
        """Initialize repository with a database connection and optional embedder."""
        self._conn = conn
        self._embedder = embedder
        self._chunk_size = chunk_size
        self._chunk_max_size = chunk_max_size

    def upsert_document(self, path: str, raw: str) -> bool:
        """Index document + split into chunks + embed. Returns True if changed."""
        doc = prepare_document(path, raw)

        cur = self._conn.cursor()
        cur.execute("SELECT content_hash FROM documents WHERE path = ?", (doc["path"],))
        row = cur.fetchone()
        if row and row[0] == doc["content_hash"]:
            return False

        # Upsert na tabela base
        cur.execute(
            """
            INSERT INTO documents (path, title, content, content_hash, metadata)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                title=excluded.title,
                content=excluded.content,
                content_hash=excluded.content_hash,
                metadata=excluded.metadata,
                updated_at=CURRENT_TIMESTAMP
        """,
            (
                doc["path"],
                doc["title"],
                doc["content"],
                doc["content_hash"],
                doc.get("metadata", "{}")
                if isinstance(doc.get("metadata"), str)
                else json.dumps(doc.get("metadata", {})),
            ),
        )

        # Sincronizar FTS5. Remove antigo e reinsere.
        cur.execute("DELETE FROM documents_fts WHERE path = ?", (doc["path"],))
        cur.execute(
            """
            INSERT INTO documents_fts (path, title, content)
            VALUES (?, ?, ?)
        """,
            (doc["path"], doc["title"], doc["content"]),
        )

        # Sincronizar topics. Remove antigo para evitar órfãos/duplicados se o slug mudou.
        cur.execute("DELETE FROM topics WHERE doc_path = ?", (doc["path"],))

        # Upsert em topics
        if doc.get("slug"):
            cur.execute(
                """
                INSERT INTO topics (slug, title, description, category, doc_path, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    title=excluded.title,
                    description=excluded.description,
                    category=excluded.category,
                    doc_path=excluded.doc_path,
                    sort_order=excluded.sort_order,
                    updated_at=CURRENT_TIMESTAMP
            """,
                (
                    doc["slug"],
                    doc["title"],
                    doc["description"],
                    doc["category"],
                    doc["path"],
                    doc["sort_order"],
                ),
            )

        # Delete old chunk embeddings before deleting chunks (FK constraint)
        with suppress(sqlite3.OperationalError):
            cur.execute(
                "DELETE FROM chunk_embeddings"
                " WHERE chunk_id IN (SELECT id FROM chunks WHERE doc_path = ?)",
                (doc["path"],),
            )

        # Delete old chunks and chunks_fts
        cur.execute("DELETE FROM chunks_fts WHERE doc_path = ?", (doc["path"],))
        cur.execute("DELETE FROM chunks WHERE doc_path = ?", (doc["path"],))

        # Split content into chunks
        chunks = split_document(
            doc["content"],
            preferred_size=self._chunk_size,
            max_size=self._chunk_max_size,
        )

        # Collect texts for batch embedding
        chunk_ids: list[int] = []
        chunk_texts: list[str] = []

        for chunk in chunks:
            cur.execute(
                "INSERT INTO chunks (doc_path, chunk_index, heading_path, content)"
                " VALUES (?, ?, ?, ?)",
                (doc["path"], chunk.index, chunk.heading_path, chunk.text),
            )
            chunk_id = cur.lastrowid
            cur.execute(
                "INSERT INTO chunks_fts (chunk_id, doc_path, heading_path, content)"
                " VALUES (?, ?, ?, ?)",
                (chunk_id, doc["path"], chunk.heading_path, chunk.text),
            )
            chunk_ids.append(chunk_id)  # type: ignore[arg-type]
            chunk_texts.append(chunk.text)

        # Embed and store vectors if embedder is configured
        if self._embedder is not None and self._embedder.dimensions > 0 and chunk_texts:
            vectors = self._embedder.embed(chunk_texts)
            for chunk_id, vector in zip(chunk_ids, vectors, strict=True):
                embedding_blob = struct.pack(f"{len(vector)}f", *vector)
                cur.execute(
                    "INSERT INTO chunk_embeddings (chunk_id, embedding) VALUES (?, ?)",
                    (chunk_id, embedding_blob),
                )

        return True

    def write_meta(self, key: str, value: str) -> None:
        """Upsert a key-value pair into the meta table."""
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO meta (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        """,
            (key, value),
        )
