"""Database initialization and connection management for the standalone SQLite architecture."""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import sqlite_vec
import structlog

from folio_sync.core.indexer import prepare_document

logger = structlog.get_logger()


def init_db(db_path: Path):
    """Inicializa o schema do SQLite."""
    logger.info("db.init", path=str(db_path))
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
        conn.commit()


@contextmanager
def connect_db(db_path: Path) -> Generator[sqlite3.Connection]:
    """Conecta ao banco e carrega a extensão sqlite-vec."""
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class SQLiteDocumentRepository:
    """Deep SQLite repository adapter for documents."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize repository with a database connection."""
        self._conn = conn

    def upsert_document(self, path: str, raw: str) -> bool:
        """Index a document into SQLite. Returns True if changed."""
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

        return True
