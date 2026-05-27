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
            slug=r["slug"],
            title=r["title"],
            description=r["description"],
            category=r["category"],
            doc_path=r["doc_path"],
            sort_order=r["sort_order"],
        )
        for r in rows
    ]
    return ListTopicsResult(topics=topics, total=len(topics))
