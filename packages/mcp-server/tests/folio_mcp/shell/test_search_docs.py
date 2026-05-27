from unittest.mock import patch

import pytest
from folio_mcp.shell.tools.search_docs import search_docs

_ROWS = [
    ("concepts/pods.md", "Pods", 0.75, "Pods are the <mark>smallest</mark> units."),
    ("concepts/services.md", "Services", 0.50, "Services <mark>expose</mark> pods."),
]


async def test_search_docs_returns_ranked_matches(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = _ROWS

    with patch("folio_mcp.shell.tools.search_docs.conn", mock_conn_ctx):
        result = await search_docs("pods scheduling")

    assert result.query == "pods scheduling"
    assert len(result.matches) == 2
    assert result.matches[0].rank == pytest.approx(0.75)


async def test_search_docs_empty_results(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = []

    with patch("folio_mcp.shell.tools.search_docs.conn", mock_conn_ctx):
        result = await search_docs("xyznonexistent")

    assert result.matches == []


async def test_search_docs_clamps_limit(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = []

    with patch("folio_mcp.shell.tools.search_docs.conn", mock_conn_ctx):
        await search_docs("pods", limit=9999)

    params = mock_cursor.execute.call_args.args[1]
    assert params[-1] <= 50


async def test_search_docs_minimum_limit(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = []

    with patch("folio_mcp.shell.tools.search_docs.conn", mock_conn_ctx):
        await search_docs("pods", limit=0)

    params = mock_cursor.execute.call_args.args[1]
    assert params[-1] >= 1
