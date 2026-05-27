"""Standalone SQLite connection provider for the MCP server."""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import sqlite_vec
import structlog
from folio_embeddings import Embedder, create_embedder

from folio_mcp.shell.config import settings

logger = structlog.get_logger()

# We expect the SQLite DB to be at /app/folio.sqlite in docker or current dir.
DB_PATH = os.getenv("FOLIO_MCP_DB_PATH", "folio.sqlite")


@contextmanager
def conn() -> Generator[sqlite3.Connection]:
    """Yield a connection to the SQLite database with sqlite-vec enabled."""
    if not Path(DB_PATH).exists():
        raise FileNotFoundError(f"Database file not found: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    try:
        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)

        # Enable FTS5 snippet and bm25 functions if needed, though they are built-in usually.
        connection.row_factory = sqlite3.Row
        yield connection
    finally:
        connection.close()


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Return the configured Embedder, validating it matches what was used for indexing."""
    provider = settings.get("embedder", "none")
    model = settings.get("embedder_model", "")
    embedder = create_embedder(provider, model)

    if provider != "none":
        _validate_embedder_model(embedder.model_id)

    return embedder


def _validate_embedder_model(configured_model_id: str) -> None:
    """Raise if configured embedder model differs from what was used to index."""
    if not Path(DB_PATH).exists():
        return  # DB not yet created, skip validation

    with conn() as c:
        cur = c.cursor()
        # meta table may not exist yet (older DB)
        try:
            cur.execute("SELECT value FROM meta WHERE key = 'embedder_model'")
            row = cur.fetchone()
        except Exception:
            return

    if row is None:
        return  # No embedder was used during indexing

    indexed_model = row["value"]
    if indexed_model != configured_model_id:
        raise RuntimeError(
            f"Embedder model mismatch: database was indexed with '{indexed_model}' "
            f"but FOLIO_EMBEDDER is configured as '{configured_model_id}'. "
            "Re-run 'folio-sync' with the current embedder to rebuild the index."
        )
