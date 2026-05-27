"""Test for pure SQL queries and sanitization."""

from folio_mcp.core.queries import sanitize_fts5_query


def test_sanitize_fts5_query_strips_quotes():
    """Quotes should be stripped to avoid unbalanced quote syntax errors."""
    q = 'foo "bar'
    assert sanitize_fts5_query(q) == "foo bar"

    q2 = "foo 'bar'"
    assert sanitize_fts5_query(q2) == "foo bar"


def test_sanitize_fts5_query_strips_special_chars():
    """Special FTS5 characters should be removed."""
    q = "foo * bar ^ baz ~"
    assert sanitize_fts5_query(q) == "foo bar baz"


def test_sanitize_fts5_query_collapses_whitespace():
    """Extra whitespace should be collapsed."""
    q = "  foo   bar \t baz  "
    assert sanitize_fts5_query(q) == "foo bar baz"
