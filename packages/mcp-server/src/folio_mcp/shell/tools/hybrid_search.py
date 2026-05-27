"""Tool: hybrid_search. Combines BM25 and semantic similarity via RRF."""

from folio_core.models import HybridSearchResult

from folio_mcp.core.ranking import rrf_merge
from folio_mcp.shell.tools.lexical_search import lexical_search
from folio_mcp.shell.tools.semantic_search import semantic_search


def hybrid_search(query: str, limit: int = 10) -> HybridSearchResult:
    """Search using both BM25 and semantic similarity, merged via Reciprocal Rank Fusion.

    Requires an embedder configured (FOLIO_EMBEDDER != none). Fails explicitly
    if no embedder is configured — use lexical_search in that case.

    Args:
        query: Search query — supports both keyword terms and natural language.
        limit: Maximum number of results (1-50).
    """
    fetch_limit = min(max(limit, 1), 50) * 3  # fetch more for RRF merging

    bm25 = lexical_search(query, limit=fetch_limit)
    semantic = semantic_search(query, limit=fetch_limit)

    merged = rrf_merge(bm25.matches, semantic.matches, k=60, limit=limit)
    return HybridSearchResult(matches=merged, query=query)
