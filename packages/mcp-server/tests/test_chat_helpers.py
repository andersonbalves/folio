"""Tests for pure helper functions in scripts/chat.py."""

import importlib.util
from pathlib import Path

import mcp.types

# Load scripts/chat.py as a module without executing main()
_spec = importlib.util.spec_from_file_location(
    "chat",
    Path(__file__).parents[3] / "scripts" / "chat.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

mcp_tool_to_ollama = _mod.mcp_tool_to_ollama
extract_result_text = _mod.extract_result_text


def _make_tool(name: str, description: str, schema: dict) -> mcp.types.Tool:
    return mcp.types.Tool(name=name, description=description, inputSchema=schema)


class TestMcpToolToOllama:
    def test_basic_conversion(self):
        tool = _make_tool(
            "search_docs",
            "Search documents by terms.",
            {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        )
        result = mcp_tool_to_ollama(tool)
        assert result["type"] == "function"
        assert result["function"]["name"] == "search_docs"
        assert result["function"]["description"] == "Search documents by terms."
        assert result["function"]["parameters"]["properties"]["query"]["type"] == "string"

    def test_none_description_becomes_empty_string(self):
        tool = mcp.types.Tool(
            name="list_topics",
            description=None,
            inputSchema={"type": "object", "properties": {}},
        )
        result = mcp_tool_to_ollama(tool)
        assert result["function"]["description"] == ""

    def test_input_schema_passed_as_parameters(self):
        schema = {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        }
        tool = _make_tool("get_document", "Get document.", schema)
        result = mcp_tool_to_ollama(tool)
        assert result["function"]["parameters"] == schema


class TestExtractResultText:
    def test_single_text_block(self):
        from fastmcp.client.client import CallToolResult

        result = CallToolResult(
            content=[mcp.types.TextContent(type="text", text="hello world")],
            structured_content=None,
            meta=None,
        )
        assert extract_result_text(result) == "hello world"

    def test_multiple_text_blocks_joined(self):
        from fastmcp.client.client import CallToolResult

        result = CallToolResult(
            content=[
                mcp.types.TextContent(type="text", text="line one"),
                mcp.types.TextContent(type="text", text="line two"),
            ],
            structured_content=None,
            meta=None,
        )
        assert extract_result_text(result) == "line one\nline two"

    def test_empty_content_returns_fallback(self):
        from fastmcp.client.client import CallToolResult

        result = CallToolResult(content=[], structured_content=None, meta=None)
        assert extract_result_text(result) == "(no text result)"

    def test_non_text_blocks_skipped(self):
        from unittest.mock import MagicMock

        from fastmcp.client.client import CallToolResult

        non_text = MagicMock()
        non_text.type = "image"
        result = CallToolResult(
            content=[non_text, mcp.types.TextContent(type="text", text="actual text")],
            structured_content=None,
            meta=None,
        )
        assert extract_result_text(result) == "actual text"
