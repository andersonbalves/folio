"""Database initialization and connection management for the standalone SQLite architecture."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import sqlite_vec
import structlog

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
