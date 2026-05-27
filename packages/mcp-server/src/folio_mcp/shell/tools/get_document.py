"""Tool: get_document."""

from folio_core.models import GetDocumentResult

from folio_mcp.core.mappers import map_document_row
from folio_mcp.core.queries import get_document_sql
from folio_mcp.shell.db import conn


def get_document(path: str) -> GetDocumentResult | None:
    """Returns the full markdown of a document.

    Use after search_docs to read the full content.

    Args:
        path: Document path, e.g., "concepts/workloads/pods.md"
    """
    sql = get_document_sql()
    with conn() as c:
        cur = c.cursor()
        cur.execute(sql, (path,))
        row = cur.fetchone()
    return map_document_row(row)
