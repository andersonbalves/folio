"""Tool: search_docs. BM25 via Postgres FTS."""

from folio_core.models import SearchDocsResult

from folio_mcp.core.mappers import map_search_rows
from folio_mcp.core.queries import sanitize_fts5_query, search_docs_sql
from folio_mcp.shell.config import settings
from folio_mcp.shell.db import conn


def search_docs(query: str, limit: int = 10) -> SearchDocsResult:
    """Search documents by terms. Returns ranked paths and snippets.

    Use after list_topics to find specific content.
    Websearch syntax: "exact phrase", OR, -excluded.

    Args:
        query: Search terms. E.g., "scheduling pods affinity"
        limit: Maximum number of results (1-50).
    """
    limit = min(max(limit, 1), settings.search.max_limit)
    sql = search_docs_sql(
        max_fragments=settings.search.snippet_max_fragments,
        max_words=settings.search.snippet_max_words,
    )
    safe_query = sanitize_fts5_query(query)
    with conn() as c:
        cur = c.cursor()
        cur.execute(sql, (safe_query, limit))
        rows = cur.fetchall()
    return map_search_rows(rows, query)
