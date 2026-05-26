"""Tests for folio_mcp/core/mappers.py — pure row-to-Pydantic mappers."""

from folio_mcp.core.mappers import map_document_row, map_search_rows, map_topic_rows

_SEARCH_ROWS = [
    ("concepts/pods.md", "Pods", 0.75, "Pods are the <mark>smallest</mark> units."),
    ("concepts/services.md", "Services", 0.50, "Services <mark>expose</mark> pods."),
]

_TOPIC_ROWS = [
    ("pods-overview", "Pods Overview", "Pods are units.", "concept", "concepts/pods.md", 10),
    ("run-app", "Run Application", "Deploy an app.", "task", "tasks/run-app.md", 5),
]

_DOCUMENT_ROW = ("concepts/pods.md", "Pods", "# Pods\n\nContent.", {"tags": ["concept"]})


def test_map_search_rows_returns_result():
    result = map_search_rows(_SEARCH_ROWS, "pods")
    assert result.query == "pods"
    assert len(result.matches) == 2
    assert result.matches[0].path == "concepts/pods.md"
    assert result.matches[0].rank == 0.75
    assert "<mark>" in result.matches[0].snippet


def test_map_search_rows_empty():
    result = map_search_rows([], "nothing")
    assert result.matches == []
    assert result.query == "nothing"


def test_map_topic_rows():
    result = map_topic_rows(_TOPIC_ROWS)
    assert result.total == 2
    assert result.topics[0].slug == "pods-overview"
    assert result.topics[1].category == "task"


def test_map_document_row_found():
    result = map_document_row(_DOCUMENT_ROW)
    assert result is not None
    assert result.path == "concepts/pods.md"
    assert result.title == "Pods"
    assert result.metadata == {"tags": ["concept"]}


def test_map_document_row_not_found():
    assert map_document_row(None) is None
