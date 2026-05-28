"""Tool: lexical_search. BM25 over chunk content via FTS5."""

import re

from folio_core.models import ChunkMatch, LexicalSearchResult

from folio_mcp.shell.config import settings
from folio_mcp.shell.db import conn


def sanitize_fts5_query(query: str) -> str:
    """Sanitize input for SQLite FTS5 MATCH clause."""
    q = re.sub(r"[/*\"\'()~^:+-]", " ", query)
    terms = [f'"{term}"' for term in q.split() if term]
    return " ".join(terms)


def lexical_search(query: str, limit: int = 10) -> LexicalSearchResult:
    """Search indexed chunks by BM25 full-text matching.

    Returns chunk-level results with heading context.
    Always available — does not require an embedder.

    Args:
        query: Search terms. Supports websearch syntax: "exact phrase", OR, -excluded.
        limit: Maximum number of results (1-50).
    """
    limit = min(max(limit, 1), settings.get("search.max_limit", 50))
    safe_query = sanitize_fts5_query(query)
    if not safe_query:
        return LexicalSearchResult(matches=[], query=query)

    sql = """
        SELECT cf.doc_path, cf.heading_path, c.chunk_index, c.content,
               -bm25(chunks_fts) AS rank
        FROM chunks_fts cf
        JOIN chunks c ON c.id = cf.chunk_id
        WHERE chunks_fts MATCH ?
        ORDER BY rank DESC
        LIMIT ?
    """
    with conn() as c_conn:
        cur = c_conn.cursor()
        cur.execute(sql, (safe_query, limit))
        rows = cur.fetchall()

    matches = [
        ChunkMatch(
            doc_path=r["doc_path"],
            heading_path=r["heading_path"],
            chunk_index=r["chunk_index"],
            content=r["content"],
            rank=float(r["rank"]),
        )
        for r in rows
    ]
    return LexicalSearchResult(matches=matches, query=query)
