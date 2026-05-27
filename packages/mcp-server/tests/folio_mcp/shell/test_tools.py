"""Integration tests for MCP shell tools, mocking the SQLite connection boundary."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from folio_embeddings.protocol import EmbedderNotConfiguredError
from folio_mcp.shell.tools.get_document import get_document
from folio_mcp.shell.tools.hybrid_search import hybrid_search
from folio_mcp.shell.tools.lexical_search import lexical_search, sanitize_fts5_query
from folio_mcp.shell.tools.list_topics import list_topics
from folio_mcp.shell.tools.search_docs import sanitize_fts5_query as old_sanitize
from folio_mcp.shell.tools.semantic_search import semantic_search

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _row_factory(data: dict) -> sqlite3.Row:
    """Build a sqlite3.Row-like object from a plain dict via an in-memory DB."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    con.execute(f"CREATE TABLE t ({cols})")
    con.execute(f"INSERT INTO t VALUES ({placeholders})", list(data.values()))
    row = con.execute("SELECT * FROM t").fetchone()
    con.close()
    return row


def _make_conn_ctx(rows: list[dict]):
    """Return a context-manager factory that yields a mock SQLite connection."""

    class _FakeCursor:
        def __init__(self, rows_: list[dict]) -> None:
            self._rows = [_row_factory(r) for r in rows_]

        def execute(self, *_args, **_kwargs):
            pass

        def fetchall(self):
            return self._rows

        def fetchone(self):
            return self._rows[0] if self._rows else None

    class _FakeConn:
        def cursor(self):
            return _FakeCursor(rows)

    @contextmanager
    def _ctx() -> Generator[_FakeConn]:
        yield _FakeConn()

    return _ctx


def _make_multi_conn_ctx(rows_per_call: list[list[dict]]):
    """Return a conn context that returns different rows on successive execute() calls."""

    class _FakeCursor:
        def __init__(self) -> None:
            self._index = 0
            self._current_rows: list[sqlite3.Row] = []

        def execute(self, *_args, **_kwargs):
            if self._index < len(rows_per_call):
                self._current_rows = [_row_factory(r) for r in rows_per_call[self._index]]
                self._index += 1

        def fetchall(self):
            return self._current_rows

        def fetchone(self):
            return self._current_rows[0] if self._current_rows else None

    class _FakeConn:
        def cursor(self):
            return _FakeCursor()

    @contextmanager
    def _ctx() -> Generator[_FakeConn]:
        yield _FakeConn()

    return _ctx


# ---------------------------------------------------------------------------
# sanitize_fts5_query (pure function — no mocking needed)
# ---------------------------------------------------------------------------


def test_sanitize_strips_special_chars():
    result = sanitize_fts5_query('hello "world" (foo)')
    assert '"hello"' in result
    assert '"world"' in result
    assert '"foo"' in result


def test_sanitize_empty_query_returns_empty():
    assert sanitize_fts5_query("") == ""


def test_sanitize_only_special_chars_returns_empty():
    assert sanitize_fts5_query('/* "()') == ""


def test_old_sanitize_still_works():
    """Ensure search_docs.sanitize_fts5_query is still importable (file kept)."""
    result = old_sanitize("hello world")
    assert '"hello"' in result


# ---------------------------------------------------------------------------
# list_topics
# ---------------------------------------------------------------------------


_TOPIC_ROW = {
    "slug": "pod",
    "title": "Pod",
    "description": "A Pod is a group of containers.",
    "category": "concept",
    "doc_path": "concepts/pod.md",
    "sort_order": 1,
}


def test_list_topics_no_filter():
    with patch("folio_mcp.shell.tools.list_topics.conn", _make_conn_ctx([_TOPIC_ROW])):
        result = list_topics()
    assert result.total == 1
    assert result.topics[0].slug == "pod"


def test_list_topics_with_category_filter():
    with patch("folio_mcp.shell.tools.list_topics.conn", _make_conn_ctx([_TOPIC_ROW])):
        result = list_topics(category="concept")
    assert result.total == 1
    assert result.topics[0].category == "concept"


def test_list_topics_empty_result():
    with patch("folio_mcp.shell.tools.list_topics.conn", _make_conn_ctx([])):
        result = list_topics()
    assert result.total == 0
    assert result.topics == []


# ---------------------------------------------------------------------------
# lexical_search
# ---------------------------------------------------------------------------


_CHUNK_ROW = {
    "doc_path": "concepts/pod.md",
    "heading_path": "Pod > Overview",
    "chunk_index": 0,
    "content": "A Pod is a group of containers.",
    "rank": 0.95,
}


def test_lexical_search_returns_matches():
    with patch("folio_mcp.shell.tools.lexical_search.conn", _make_conn_ctx([_CHUNK_ROW])):
        result = lexical_search("pod")
    assert len(result.matches) == 1
    assert result.matches[0].doc_path == "concepts/pod.md"
    assert result.matches[0].heading_path == "Pod > Overview"
    assert result.query == "pod"


def test_lexical_search_empty_query_returns_no_matches():
    result = lexical_search("")
    assert result.matches == []
    assert result.query == ""


def test_lexical_search_only_special_chars_returns_no_matches():
    result = lexical_search("/* ()")
    assert result.matches == []


def test_lexical_search_limit_clamped():
    with patch("folio_mcp.shell.tools.lexical_search.conn", _make_conn_ctx([])):
        result = lexical_search("pod", limit=0)
    assert result.matches == []


# ---------------------------------------------------------------------------
# get_document
# ---------------------------------------------------------------------------


_DOCUMENT_ROW = {
    "path": "concepts/pod.md",
    "title": "Pod",
    "content": "# Pod\nA Pod is a group of containers.",
    "metadata": '{"category": "concept"}',
}


def test_get_document_found():
    with patch("folio_mcp.shell.tools.get_document.conn", _make_conn_ctx([_DOCUMENT_ROW])):
        result = get_document("concepts/pod.md")
    assert result is not None
    assert result.path == "concepts/pod.md"
    assert result.metadata == {"category": "concept"}


def test_get_document_not_found():
    with patch("folio_mcp.shell.tools.get_document.conn", _make_conn_ctx([])):
        result = get_document("nonexistent.md")
    assert result is None


# ---------------------------------------------------------------------------
# semantic_search
# ---------------------------------------------------------------------------


_VEC_ROW = {"chunk_id": 1, "rank": 0.92}
_CHUNK_DETAIL_ROW = {
    "id": 1,
    "doc_path": "concepts/pod.md",
    "heading_path": "Pod > Overview",
    "chunk_index": 0,
    "content": "A Pod is a group of containers.",
}


def _make_mock_embedder(vector: list[float] | None = None):
    """Build a mock Embedder that returns a fixed vector."""
    embedder = MagicMock()
    vec = vector or [0.1] * 4
    embedder.embed.return_value = [vec]
    return embedder


def test_semantic_search_returns_matches():
    mock_embedder = _make_mock_embedder()
    with (
        patch("folio_mcp.shell.tools.semantic_search.get_embedder", return_value=mock_embedder),
        patch(
            "folio_mcp.shell.tools.semantic_search.conn",
            _make_multi_conn_ctx([[_VEC_ROW], [_CHUNK_DETAIL_ROW]]),
        ),
    ):
        result = semantic_search("what is a pod")
    assert len(result.matches) == 1
    assert result.matches[0].doc_path == "concepts/pod.md"
    assert result.query == "what is a pod"


def test_semantic_search_no_vec_results():
    mock_embedder = _make_mock_embedder()
    with (
        patch("folio_mcp.shell.tools.semantic_search.get_embedder", return_value=mock_embedder),
        patch(
            "folio_mcp.shell.tools.semantic_search.conn",
            _make_multi_conn_ctx([[]]),
        ),
    ):
        result = semantic_search("nothing here")
    assert result.matches == []
    assert result.query == "nothing here"


def test_semantic_search_raises_when_no_embedder():
    import pytest

    no_embedder = MagicMock()
    no_embedder.embed.side_effect = EmbedderNotConfiguredError("no embedder")
    with (
        patch("folio_mcp.shell.tools.semantic_search.get_embedder", return_value=no_embedder),
        pytest.raises(EmbedderNotConfiguredError),
    ):
        semantic_search("query")


# ---------------------------------------------------------------------------
# hybrid_search
# ---------------------------------------------------------------------------


def test_hybrid_search_merges_results():
    mock_embedder = _make_mock_embedder()
    with (
        patch("folio_mcp.shell.tools.semantic_search.get_embedder", return_value=mock_embedder),
        patch(
            "folio_mcp.shell.tools.lexical_search.conn",
            _make_conn_ctx([_CHUNK_ROW]),
        ),
        patch(
            "folio_mcp.shell.tools.semantic_search.conn",
            _make_multi_conn_ctx([[_VEC_ROW], [_CHUNK_DETAIL_ROW]]),
        ),
    ):
        result = hybrid_search("pod", limit=10)
    assert len(result.matches) >= 1
    assert result.query == "pod"


def test_hybrid_search_empty_query():
    import pytest

    no_embedder = MagicMock()
    no_embedder.embed.side_effect = EmbedderNotConfiguredError("no embedder")
    with (
        patch("folio_mcp.shell.tools.semantic_search.get_embedder", return_value=no_embedder),
        pytest.raises(EmbedderNotConfiguredError),
    ):
        hybrid_search("")


# ---------------------------------------------------------------------------
# search_docs (legacy — file kept, tests ensure coverage)
# ---------------------------------------------------------------------------


_SEARCH_ROW = {
    "path": "concepts/pod.md",
    "title": "Pod",
    "rank": 0.95,
    "snippet": "A Pod is a <mark>group</mark> of containers...",
}


def test_search_docs_returns_matches():
    from folio_mcp.shell.tools.search_docs import search_docs

    with patch("folio_mcp.shell.tools.search_docs.conn", _make_conn_ctx([_SEARCH_ROW])):
        result = search_docs("pod")
    assert len(result.matches) == 1
    assert result.matches[0].path == "concepts/pod.md"
    assert result.query == "pod"


def test_search_docs_empty_query_returns_no_matches():
    from folio_mcp.shell.tools.search_docs import search_docs

    result = search_docs("")
    assert result.matches == []


def test_search_docs_only_special_chars_returns_no_matches():
    from folio_mcp.shell.tools.search_docs import search_docs

    result = search_docs("/* ()")
    assert result.matches == []
