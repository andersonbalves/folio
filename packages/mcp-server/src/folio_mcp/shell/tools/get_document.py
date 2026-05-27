"""Tool: get_document."""

from folio_core.models import GetDocumentResult

from folio_mcp.shell.db import conn


def get_document(path: str) -> GetDocumentResult | None:
    """Returns the full markdown of a document.

    Use after search_docs to read the full content.

    Args:
        path: Document path, e.g., "concepts/workloads/pods.md"
    """
    sql = "SELECT path, title, content, metadata FROM documents WHERE path = ?"
    with conn() as c:
        cur = c.cursor()
        cur.execute(sql, (path,))
        row = cur.fetchone()

    if row is None:
        return None
    import json

    raw_meta = row["metadata"]
    metadata = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
    return GetDocumentResult(
        path=row["path"],
        title=row["title"],
        content=row["content"],
        metadata=metadata,
    )
