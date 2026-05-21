"""End-to-end tests — require running LocalStack and Postgres.

Run only after: make up && make migrate && make seed
"""

import pytest

pytestmark = pytest.mark.integration


async def test_full_sync_indexes_s3_docs():
    from folio_sync.db import close_pool, conn
    from folio_sync.indexer import full_sync

    stats = await full_sync()
    await close_pool()

    assert stats["scanned"] > 0
    assert stats["indexed"] >= 0

    async with conn() as c, c.cursor() as cur:
        await cur.execute("SELECT COUNT(*) FROM documents")
        (count,) = await cur.fetchone()

    await close_pool()
    assert count == stats["scanned"] - stats["skipped"] + stats["indexed"]


async def test_mcp_search_returns_results():
    from folio_mcp.db import close_pool
    from folio_mcp.tools.search_docs import search_docs

    result = await search_docs("pods scheduling")
    await close_pool()

    assert len(result.matches) > 0
    assert result.matches[0].rank > 0
