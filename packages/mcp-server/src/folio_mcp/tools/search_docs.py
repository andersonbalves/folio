"""Tool: search_docs. BM25 via Postgres FTS."""

from folio_core.models import SearchDocsResult, SearchMatch
from folio_mcp.config import settings
from folio_mcp.db import conn


async def search_docs(query: str, limit: int = 10) -> SearchDocsResult:
    """Search documents by terms. Returns ranked paths and snippets.

    Use after list_topics to find specific content.
    Search is lexical (BM25): combine exact technical terms.
    Websearch syntax: "exact phrase", OR, -excluded.

    Args:
        query: Search terms. E.g., "scheduling pods affinity"
        limit: Maximum number of results (1-50).
    """
    limit = min(max(limit, 1), settings.search.max_limit)

    sql = f"""
        SELECT
            path, title,
            ts_rank_cd(tsv, q) AS rank,
            ts_headline('simple', content, q,
                'StartSel=<mark>, StopSel=</mark>, '
                'MaxFragments={settings.search.snippet_max_fragments}, '
                'MaxWords={settings.search.snippet_max_words}, MinWords=10'
            ) AS snippet
        FROM documents,
             websearch_to_tsquery('simple', %s) AS q
        WHERE tsv @@ q
        ORDER BY rank DESC
        LIMIT %s
    """

    async with conn() as c, c.cursor() as cur:
        await cur.execute(sql, (query, limit))
        rows = await cur.fetchall()

    matches = [SearchMatch(path=r[0], title=r[1], rank=float(r[2]), snippet=r[3]) for r in rows]
    return SearchDocsResult(matches=matches, query=query)
