"""Tests for rrf_merge — pure function, no mocks."""

from folio_core.models import ChunkMatch
from folio_mcp.core.ranking import rrf_merge


def _match(doc_path: str, chunk_index: int, rank: float = 1.0) -> ChunkMatch:
    return ChunkMatch(
        doc_path=doc_path, heading_path="", chunk_index=chunk_index, content="x", rank=rank
    )


def test_rrf_scores_chunks_in_both_lists_higher():
    bm25 = [_match("a.md", 0, 1.0), _match("b.md", 0, 0.5)]
    vec = [_match("a.md", 0, 1.0), _match("c.md", 0, 0.5)]
    result = rrf_merge(bm25, vec, k=60, limit=10)
    keys = [(r.doc_path, r.chunk_index) for r in result]
    # a.md/0 appears in both lists → should rank first
    assert keys[0] == ("a.md", 0)


def test_rrf_returns_at_most_limit_results():
    bm25 = [_match(f"doc{i}.md", 0) for i in range(20)]
    vec = [_match(f"doc{i}.md", 0) for i in range(20)]
    result = rrf_merge(bm25, vec, limit=5)
    assert len(result) <= 5


def test_rrf_empty_inputs():
    assert rrf_merge([], [], limit=10) == []


def test_rrf_only_bm25():
    bm25 = [_match("a.md", 0), _match("b.md", 1)]
    result = rrf_merge(bm25, [], limit=10)
    assert len(result) == 2


def test_rrf_rank_field_contains_rrf_score():
    bm25 = [_match("a.md", 0)]
    result = rrf_merge(bm25, [], k=60, limit=10)
    expected = 1.0 / (60 + 1)
    assert abs(result[0].rank - expected) < 1e-10


def test_rrf_different_chunks_same_doc():
    bm25 = [_match("a.md", 0), _match("a.md", 1)]
    vec = [_match("a.md", 1), _match("a.md", 2)]
    result = rrf_merge(bm25, vec, limit=10)
    keys = [(r.doc_path, r.chunk_index) for r in result]
    # a.md/1 in both lists → should be highest
    assert keys[0] == ("a.md", 1)
    assert len(result) == 3  # 0, 1, 2
