import pytest
from folio_mcp.handler import mcp


@pytest.mark.asyncio
async def test_mcp_instance():
    # Assert
    assert mcp.name == "folio"

    # FastMCP uses its internal tool registry, we can check the names
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "list_topics" in tool_names
    assert "search_docs" in tool_names
    assert "get_document" in tool_names
