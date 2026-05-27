"""I/O layer: reads from S3, writes to Postgres. Calls core/indexer.py."""

import structlog
from folio_core import postgres_sql

from folio_sync.core.indexer import prepare_document
from folio_sync.shell.config import settings
from folio_sync.shell.db import conn
from folio_sync.shell.s3_client import iter_markdowns

logger = structlog.get_logger()


async def upsert_document(path: str, raw: str) -> bool:
    """Index a document. Returns True if the document changed."""
    doc = prepare_document(path, raw)

    async with conn() as c:
        async with c.cursor() as cur:
            await cur.execute(
                *postgres_sql(t"SELECT content_hash FROM documents WHERE path = {doc['path']}")
            )
            row = await cur.fetchone()
            if row and row[0] == doc["content_hash"]:
                return False

            await cur.execute(
                *postgres_sql(t"""
                INSERT INTO documents (path, title, content, content_hash, metadata)
                VALUES ({doc["path"]}, {doc["title"]}, {doc["content"]},
                        {doc["content_hash"]}, {doc["metadata"]}::jsonb)
                ON CONFLICT (path) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    content_hash = EXCLUDED.content_hash,
                    metadata = EXCLUDED.metadata,
                    updated_at = now()
                """)
            )

            await cur.execute(
                *postgres_sql(t"""
                INSERT INTO topics (slug, title, description, category, doc_path, sort_order)
                VALUES ({doc["slug"]}, {doc["title"]}, {doc["description"]},
                        {doc["category"]}, {doc["path"]}, {doc["sort_order"]})
                ON CONFLICT (slug) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    doc_path = EXCLUDED.doc_path,
                    sort_order = EXCLUDED.sort_order,
                    updated_at = now()
                """)
            )

        await c.commit()

    logger.info("doc.indexed", path=path)
    return True


async def full_sync() -> dict:
    """Sync all documents from S3. Returns stats dict."""
    stats = {"scanned": 0, "indexed": 0, "skipped": 0}
    async for key, content in iter_markdowns(settings.s3.bucket, settings.s3.prefix):
        stats["scanned"] += 1
        changed = await upsert_document(key, content)
        if changed:
            stats["indexed"] += 1
        else:
            stats["skipped"] += 1
    logger.info("sync.full_complete", **stats)
    return stats
