"""Standalone SQLite connection provider for the MCP server."""

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


def _db_path() -> str:
    return str(settings.get("mcp.db_path", "folio.sqlite"))


@contextmanager
def conn() -> Generator[sqlite3.Connection]:
    """Yield a connection to the SQLite database with sqlite-vec enabled."""
    path = _db_path()
    if not Path(path).exists():
        raise FileNotFoundError(f"Database file not found: {path}")

    connection = sqlite3.connect(path)
    try:
        connection.enable_load_extension(True)
        sqlite_vec.load(connection)
        connection.enable_load_extension(False)
        connection.row_factory = sqlite3.Row
        yield connection
    finally:
        connection.close()


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Return the configured Embedder, validating it matches what was used for indexing."""
    provider = settings.get("embedder.provider", "none")
    model = settings.get("embedder.model", "")
    embedder = create_embedder(
        provider,
        model,
        base_url=settings.get("embedder.ollama_host"),
        timeout=float(settings.get("embedder.ollama_timeout", 60.0)),
        api_key=settings.get("embedder.api_key"),
    )

    if provider != "none":
        _validate_embedder_model(embedder.model_id)

    return embedder


def _validate_embedder_model(configured_model_id: str) -> None:
    """Raise if configured embedder model differs from what was used to index."""
    path = _db_path()
    if not Path(path).exists():
        return

    with conn() as c:
        cur = c.cursor()
        try:
            cur.execute("SELECT value FROM meta WHERE key = 'embedder_model'")
            row = cur.fetchone()
        except Exception:
            return

    if row is None:
        return

    indexed_model = row["value"]
    if indexed_model != configured_model_id:
        raise RuntimeError(
            f"Embedder model mismatch: database was indexed with '{indexed_model}' "
            f"but FOLIO_EMBEDDER__PROVIDER is configured as '{configured_model_id}'. "
            "Re-run 'folio-sync' with the current embedder to rebuild the index."
        )
