"""Tool: list_topics."""

from folio_core.models import ListTopicsResult, Topic
from folio_mcp.db import conn


async def list_topics(category: str | None = None) -> ListTopicsResult:
    """Lists available topics in the documentation.

    Use this tool first to discover the platform's internal vocabulary
    (starter names, ADRs, concepts). Then use search_docs or
    get_document with the exact terms from the index.

    Args:
        category: Filter by category (e.g., "concept", "task", "starter", "adr").
                  Omit to list everything.
    """
    if category:
        query = """
            SELECT slug, title, description, category, doc_path, sort_order
            FROM topics
            WHERE category = %s
            ORDER BY category, sort_order, title
        """
        params = (category,)
    else:
        query = """
            SELECT slug, title, description, category, doc_path, sort_order
            FROM topics
            ORDER BY category, sort_order, title
        """
        params = ()

    async with conn() as c, c.cursor() as cur:
        await cur.execute(query, params)
        rows = await cur.fetchall()

    topics = [
        Topic(
            slug=r[0], title=r[1], description=r[2], category=r[3], doc_path=r[4], sort_order=r[5]
        )
        for r in rows
    ]
    return ListTopicsResult(topics=topics, total=len(topics))
