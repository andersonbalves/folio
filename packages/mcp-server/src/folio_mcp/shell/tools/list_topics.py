"""Tool: list_topics."""

from folio_core.models import ListTopicsResult, Topic

from folio_mcp.shell.db import conn


def list_topics(category: str | None = None) -> ListTopicsResult:
    """Lists available topics in the documentation.

    Use first to discover the platform's internal vocabulary.

    Args:
        category: Filter by category (e.g., "concept", "task", "starter", "adr").
    """
    if category:
        sql = (
            "SELECT slug, title, description, category, doc_path, sort_order "
            "FROM topics WHERE category = ? ORDER BY category, sort_order, title"
        )
        params = (category,)
    else:
        sql = (
            "SELECT slug, title, description, category, doc_path, sort_order "
            "FROM topics ORDER BY category, sort_order, title"
        )
        params = ()
        
    with conn() as c:
        cur = c.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        
    topics = [
        Topic(
            slug=r[0],
            title=r[1],
            description=r[2],
            category=r[3],
            doc_path=r[4],
            sort_order=r[5],
        )
        for r in rows
    ]
    return ListTopicsResult(topics=topics, total=len(topics))
