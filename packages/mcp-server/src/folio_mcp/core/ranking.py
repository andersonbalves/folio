"""Pure ranking utilities for hybrid search."""

from folio_core.models import ChunkMatch


def rrf_merge(
    bm25_results: list[ChunkMatch],
    vector_results: list[ChunkMatch],
    k: int = 60,
    limit: int = 10,
) -> list[ChunkMatch]:
    """Merge two ranked lists using Reciprocal Rank Fusion.

    RRF score = sum of 1/(k + rank) for each list where the chunk appears.
    Rank is 1-based position in the list.

    Args:
        bm25_results: Results from lexical search, ordered by rank desc.
        vector_results: Results from vector search, ordered by rank desc.
        k: RRF constant (default 60).
        limit: Max results to return.

    Returns:
        Merged list of ChunkMatch ordered by RRF score descending.
        Each result's `rank` field contains the RRF score.
    """
    scores: dict[tuple[str, int], float] = {}  # (doc_path, chunk_index) -> rrf_score
    by_key: dict[tuple[str, int], ChunkMatch] = {}

    for rank_1based, match in enumerate(bm25_results, start=1):
        key = (match.doc_path, match.chunk_index)
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank_1based)
        by_key[key] = match

    for rank_1based, match in enumerate(vector_results, start=1):
        key = (match.doc_path, match.chunk_index)
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank_1based)
        if key not in by_key:
            by_key[key] = match

    sorted_keys = sorted(scores.keys(), key=scores.__getitem__, reverse=True)[:limit]
    return [
        ChunkMatch(
            doc_path=by_key[key].doc_path,
            heading_path=by_key[key].heading_path,
            chunk_index=by_key[key].chunk_index,
            content=by_key[key].content,
            rank=scores[key],
        )
        for key in sorted_keys
    ]
