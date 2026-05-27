from unittest.mock import patch

from folio_mcp.shell.tools.get_document import get_document

_ROW = ("concepts/pods.md", "Pods", "# Pods\n\nPods are units.", {"tags": ["concept"]})


async def test_get_document_found(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = _ROW

    with patch("folio_mcp.shell.tools.get_document.conn", mock_conn_ctx):
        result = await get_document("concepts/pods.md")

    assert result is not None
    assert result.path == "concepts/pods.md"
    assert result.metadata == {"tags": ["concept"]}


async def test_get_document_not_found(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = None

    with patch("folio_mcp.shell.tools.get_document.conn", mock_conn_ctx):
        result = await get_document("nonexistent.md")

    assert result is None
