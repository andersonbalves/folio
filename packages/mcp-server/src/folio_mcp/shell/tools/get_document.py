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
    return GetDocumentResult(path=row[0], title=row[1], content=row[2], metadata=row[3])
