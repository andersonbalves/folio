"""Tool: list_topics."""

from folio_core.models import ListTopicsResult

from folio_mcp.core.mappers import map_topic_rows
from folio_mcp.core.queries import list_topics_sql
from folio_mcp.shell.db import conn


def list_topics(category: str | None = None) -> ListTopicsResult:
    """Lists available topics in the documentation.

    Use first to discover the platform's internal vocabulary.

    Args:
        category: Filter by category (e.g., "concept", "task", "starter", "adr").
    """
    sql, params = list_topics_sql(category)
    with conn() as c:
        cur = c.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
    return map_topic_rows([dict(r) for r in rows])
