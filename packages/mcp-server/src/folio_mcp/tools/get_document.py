"""Tool: get_document."""

from folio_core import postgres_sql
from folio_core.models import GetDocumentResult
from folio_mcp.db import conn


async def get_document(path: str) -> GetDocumentResult | None:
    """Returns the full markdown of a document.

    Use after search_docs to read the full content.
    Snippets from search_docs are indicative — read the entire
    file for a high-quality response.

    Args:
        path: Document path, e.g., "concepts/workloads/pods.md"
    """
    async with conn() as c, c.cursor() as cur:
        await cur.execute(
            *postgres_sql(
                t"SELECT path, title, content, metadata FROM documents WHERE path = {path}"
            )
        )
        row = await cur.fetchone()

    if row is None:
        return None

    return GetDocumentResult(
        path=row[0],
        title=row[1],
        content=row[2],
        metadata=row[3],
    )
