from unittest.mock import patch

from folio_mcp.tools.list_topics import list_topics

_ROWS = [
    ("pods-overview", "Pods Overview", "Pods are units.", "concept", "concepts/pods.md", 10),
    ("services", "Services", "Services expose pods.", "concept", "concepts/services.md", 20),
    ("run-app", "Run Application", "Deploy an app.", "task", "tasks/run-app.md", 5),
]


async def test_list_topics_all(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = _ROWS

    with patch("folio_mcp.tools.list_topics.conn", mock_conn_ctx):
        result = await list_topics()

    assert result.total == 3
    assert result.topics[0].slug == "pods-overview"
    assert result.topics[2].category == "task"


async def test_list_topics_filtered_by_category(mock_conn_ctx, mock_cursor):
    concept_rows = [r for r in _ROWS if r[3] == "concept"]
    mock_cursor.fetchall.return_value = concept_rows

    with patch("folio_mcp.tools.list_topics.conn", mock_conn_ctx):
        result = await list_topics(category="concept")

    assert result.total == 2
    assert all(t.category == "concept" for t in result.topics)
    # Verify category param was passed to query
    call_args = mock_cursor.execute.call_args
    assert "concept" in call_args.args[1]


async def test_list_topics_empty(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = []

    with patch("folio_mcp.tools.list_topics.conn", mock_conn_ctx):
        result = await list_topics()

    assert result.total == 0
    assert result.topics == []
