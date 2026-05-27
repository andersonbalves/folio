"""CLI entrypoint for standalone Folio indexing."""

import argparse
import json
import sys
from pathlib import Path

import structlog

from folio_sync.core.indexer import prepare_document
from folio_sync.shell.db import connect_db, init_db

logger = structlog.get_logger()


def upsert_document(conn, path: str, raw: str) -> bool:
    """Index a document into SQLite. Returns True if changed."""
    doc = prepare_document(path, raw)

    cur = conn.cursor()
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
            json.dumps(doc.get("metadata", {})),
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


def main():
    """Run the main CLI indexer logic."""
    parser = argparse.ArgumentParser(description="Indexador de documentos para o Folio Standalone")
    parser.add_argument("data_dir", type=Path, help="Diretório contendo os arquivos .md")
    parser.add_argument("db_path", type=Path, help="Caminho do arquivo SQLite de destino")
    args = parser.parse_args()

    data_dir = args.data_dir
    db_path = args.db_path

    if not data_dir.exists() or not data_dir.is_dir():
        logger.error("cli.data_dir_not_found", data_dir=str(data_dir))
        sys.exit(1)

    # Inicializa o banco (Auto-inicialização do Schema)
    init_db(db_path)

    stats = {"scanned": 0, "indexed": 0, "skipped": 0}

    with connect_db(db_path) as conn:
        for md_file in data_dir.rglob("*.md"):
            stats["scanned"] += 1
            rel_path = str(md_file.relative_to(data_dir))
            try:
                raw_content = md_file.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.error("file.read_error", path=rel_path, error=str(e))
                continue

            changed = upsert_document(conn, rel_path, raw_content)
            if changed:
                stats["indexed"] += 1
                logger.info("doc.indexed", path=rel_path)
            else:
                stats["skipped"] += 1

        conn.commit()

    logger.info("sync.full_complete", **stats)


if __name__ == "__main__":
    main()
