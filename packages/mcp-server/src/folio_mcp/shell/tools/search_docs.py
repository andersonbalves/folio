"""Tool: search_docs. BM25 via Postgres FTS."""

import re

from folio_core.models import SearchDocsResult, SearchMatch

from folio_mcp.shell.config import settings
from folio_mcp.shell.db import conn


def sanitize_fts5_query(query: str) -> str:
    """Sanitize user input for SQLite FTS5 MATCH clause to prevent syntax errors."""
    q = re.sub(r"[/*\"\'()~^:+-]", " ", query)
    terms = [f'"{term}"' for term in q.split() if term]
    return " ".join(terms)


def search_docs(query: str, limit: int = 10) -> SearchDocsResult:
    """Search documents by terms. Returns ranked paths and snippets.

    Use after list_topics to find specific content.
    Websearch syntax: "exact phrase", OR, -excluded.

    Args:
        query: Search terms. E.g., "scheduling pods affinity"
        limit: Maximum number of results (1-50).
    """
    limit = min(max(limit, 1), settings.search.max_limit)
    safe_query = sanitize_fts5_query(query)

    if not safe_query:
        return SearchDocsResult(matches=[], query=query)

    sql = """
        SELECT
            path, title,
            -bm25(documents_fts) AS rank,
            snippet(documents_fts, -1, '<mark>', '</mark>', '...', 64) AS snippet
        FROM documents_fts
        WHERE documents_fts MATCH ?
        ORDER BY rank DESC
        LIMIT ?
    """

    with conn() as c:
        cur = c.cursor()
        cur.execute(sql, (safe_query, limit))
        rows = cur.fetchall()

    matches = [
        SearchMatch(
            path=r["path"],
            title=r["title"],
            rank=float(r["rank"]),
            snippet=r["snippet"],
        )
        for r in rows
    ]
    return SearchDocsResult(matches=matches, query=query)
