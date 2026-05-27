import pytest
from folio_mcp.shell.handler import mcp


@pytest.mark.asyncio
async def test_mcp_instance():
    assert mcp.name == "folio"
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "list_topics" in tool_names
    assert "lexical_search" in tool_names
    assert "semantic_search" in tool_names
    assert "hybrid_search" in tool_names
    assert "get_document" in tool_names
    assert "search_docs" not in tool_names  # renamed
