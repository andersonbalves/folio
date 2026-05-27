"""Standalone SQLite connection provider for the MCP server."""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

import sqlite_vec
import structlog

logger = structlog.get_logger()

# We expect the SQLite DB to be at /app/folio.sqlite in docker or current dir.
DB_PATH = os.getenv("FOLIO_MCP_DB_PATH", "folio.sqlite")


@contextmanager
def conn() -> Generator[sqlite3.Connection]:
    """Yield a connection to the SQLite database with sqlite-vec enabled."""
    connection = sqlite3.connect(DB_PATH)
    connection.enable_load_extension(True)
    sqlite_vec.load(connection)
    connection.enable_load_extension(False)

    # Enable FTS5 snippet and bm25 functions if needed, though they are built-in usually.
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()
