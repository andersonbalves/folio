"""Integration tests for MCP shell tools, mocking the SQLite connection boundary."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import patch

from folio_mcp.shell.tools.get_document import get_document
from folio_mcp.shell.tools.list_topics import list_topics
from folio_mcp.shell.tools.search_docs import sanitize_fts5_query, search_docs

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
# search_docs
# ---------------------------------------------------------------------------


_SEARCH_ROW = {
    "path": "concepts/pod.md",
    "title": "Pod",
    "rank": 0.95,
    "snippet": "A Pod is a <mark>group</mark> of containers...",
}


def test_search_docs_returns_matches():
    with patch("folio_mcp.shell.tools.search_docs.conn", _make_conn_ctx([_SEARCH_ROW])):
        result = search_docs("pod")
    assert len(result.matches) == 1
    assert result.matches[0].path == "concepts/pod.md"
    assert result.query == "pod"


def test_search_docs_empty_query_returns_no_matches():
    result = search_docs("")
    assert result.matches == []
    assert result.query == ""


def test_search_docs_only_special_chars_returns_no_matches():
    result = search_docs("/* ()")
    assert result.matches == []


def test_search_docs_limit_clamped():
    with patch("folio_mcp.shell.tools.search_docs.conn", _make_conn_ctx([])):
        result = search_docs("pod", limit=0)
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
