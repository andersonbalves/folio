# /// script
# requires-python = ">=3.14"
# dependencies = ["ollama", "fastmcp>=3.3.1"]
# ///
"""Conversational REPL: Ollama model + folio-mcp tools via MCP stdio."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

import mcp.types
import ollama
from fastmcp import Client
from fastmcp.client.client import CallToolResult

_PROJECT_ROOT = Path(__file__).parent.parent


def mcp_tool_to_ollama(tool: mcp.types.Tool) -> dict[str, Any]:
    """Convert an MCP tool schema to Ollama's tool format."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


def extract_result_text(result: CallToolResult) -> str:
    """Extract concatenated text from a CallToolResult."""
    parts = [block.text for block in result.content if isinstance(block, mcp.types.TextContent)]
    return "\n".join(parts) if parts else "(no text result)"


class MCPBridge:
    """Wraps a connected FastMCP Client, exposing tool list/call operations."""

    def __init__(self, client: Client) -> None:
        """Store the already-connected MCP client."""
        self._client = client

    async def list_tools(self) -> list[mcp.types.Tool]:
        """Return all tools from the connected MCP server."""
        return await self._client.list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a named tool and return its text result."""
        try:
            result = await self._client.call_tool(name, arguments, raise_on_error=False)
            return extract_result_text(result)
        except Exception as exc:
            return f"[tool error: {exc}]"


DEFAULT_MODEL = "qwen3:8b"
DEFAULT_MCP_COMMAND = "uv run folio-mcp"
DEFAULT_SYSTEM = (
    "You are a helpful assistant with access to the Folio internal knowledge base. "
    "When the user asks about documentation, always use the available tools. "
    "Recommended flow: 1) list_topics to discover vocabulary, "
    "2) search_docs with exact terms, 3) get_document to read full content."
)


class OllamaAgent:
    """Drives the Ollama tool-calling agent loop with persistent message history."""

    def __init__(
        self,
        model: str,
        bridge: MCPBridge,
        tools: list[mcp.types.Tool],
        system: str = DEFAULT_SYSTEM,
    ) -> None:
        """Initialise with model, bridge, tools and an optional system prompt."""
        self._model = model
        self._bridge = bridge
        self._ollama_tools = [mcp_tool_to_ollama(t) for t in tools]
        self._messages: list[Any] = [{"role": "system", "content": system}]

    async def run(self, user_msg: str) -> str:
        """Append user message and run the agent loop until a final text response."""
        self._messages.append({"role": "user", "content": user_msg})

        while True:
            response = await asyncio.to_thread(
                ollama.chat,
                model=self._model,
                messages=self._messages,
                tools=self._ollama_tools,
            )
            assistant_msg = response.message
            self._messages.append(assistant_msg)

            if not assistant_msg.tool_calls:
                return assistant_msg.content or ""

            for tool_call in assistant_msg.tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments or {}
                print(f"  [tool: {name}({args})]")  # noqa: T201
                result_text = await self._bridge.call_tool(name, args)
                truncated = result_text[:500] + "…" if len(result_text) > 500 else result_text
                print(f"  → {truncated}")  # noqa: T201
                self._messages.append({"role": "tool", "content": result_text})


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Chat with folio docs via Ollama + MCP")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model (default: qwen3:8b)")
    parser.add_argument(
        "--mcp-command", default=DEFAULT_MCP_COMMAND, help="Command to spawn MCP server"
    )
    parser.add_argument("--system", default=DEFAULT_SYSTEM, help="System prompt override")
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    asyncio.run(main_async(args))


async def main_async(args: argparse.Namespace) -> None:
    """Run the chat REPL."""


if __name__ == "__main__":
    main()
