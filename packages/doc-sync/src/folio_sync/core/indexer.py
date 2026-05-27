"""Pure document preparation. No I/O — returns a dict ready for DB upsert."""

import json

from folio_sync.core.categorizer import (
    infer_category,
    infer_description,
    infer_slug,
    infer_sort_order,
    infer_title,
)
from folio_sync.core.hasher import content_hash
from folio_sync.core.parser import parse_markdown


def prepare_document(path: str, raw: str) -> dict:
    """Derive all indexable fields from a raw markdown string."""
    parsed = parse_markdown(raw)
    h = content_hash(raw)
    fm = parsed.front_matter
    return {
        "path": path,
        "content": parsed.body,
        "content_hash": h,
        "title": infer_title(path, fm, parsed.body),
        "slug": infer_slug(path, fm),
        "category": infer_category(path),
        "description": infer_description(fm, parsed.body),
        "sort_order": infer_sort_order(path, fm),
        "metadata": json.dumps({"tags": fm.get("tags", [])}),
    }
