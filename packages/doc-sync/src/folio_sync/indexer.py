"""Orchestrates core (pure) + DB (shell) for indexing."""

import json

import structlog
from folio_core import postgres_sql
from folio_core.categorizer import (
    infer_category,
    infer_description,
    infer_slug,
    infer_sort_order,
    infer_title,
)
from folio_core.hasher import content_hash
from folio_core.parser import parse_markdown

from folio_sync.config import settings
from folio_sync.db import conn
from folio_sync.s3_client import iter_markdowns

logger = structlog.get_logger()


async def upsert_document(path: str, raw: str) -> bool:
    """Indexes a document. Returns True if there was a change."""
    parsed = parse_markdown(raw)
    h = content_hash(raw)
    fm = parsed.front_matter

    title = infer_title(path, fm, parsed.body)
    slug = infer_slug(path, fm)
    category = infer_category(path)
    description = infer_description(fm, parsed.body)
    sort_order = infer_sort_order(path, fm)
    metadata = {"tags": fm.get("tags", [])}

    async with conn() as c:
        async with c.cursor() as cur:
            # Check hash
            await cur.execute(
                *postgres_sql(t"SELECT content_hash FROM documents WHERE path = {path}")
            )
            row = await cur.fetchone()
            if row and row[0] == h:
                return False

            # Upsert document
            await cur.execute(
                *postgres_sql(t"""
                INSERT INTO documents (path, title, content, content_hash, metadata)
                VALUES ({path}, {title}, {parsed.body}, {h}, {json.dumps(metadata)}::jsonb)
                ON CONFLICT (path) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    content_hash = EXCLUDED.content_hash,
                    metadata = EXCLUDED.metadata,
                    updated_at = now()
                """)
            )

            # Upsert topic
            await cur.execute(
                *postgres_sql(t"""
                INSERT INTO topics (slug, title, description, category, doc_path, sort_order)
                VALUES ({slug}, {title}, {description}, {category}, {path}, {sort_order})
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
    """Synchronizes everything from the S3 bucket. Returns stats."""
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
