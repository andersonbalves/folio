"""CLI entry point for the doc-sync service."""

import asyncio

import structlog

from folio_sync.shell.db import close_pool
from folio_sync.shell.indexer import full_sync

logger = structlog.get_logger()


async def _run() -> None:
    """Run full sync and close pool."""
    stats = await full_sync()
    await close_pool()
    logger.info("sync.cli_complete", **stats)


def main() -> None:
    """CLI entry point — runs a full S3→Postgres sync."""
    asyncio.run(_run())
