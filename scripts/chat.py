# /// script
# requires-python = ">=3.14"
# dependencies = ["ollama", "fastmcp>=3.3.1"]
# ///
"""Conversational REPL: Ollama model + folio-mcp tools via MCP stdio."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_MODEL = "qwen3:8b"
DEFAULT_MCP_COMMAND = "uv run folio-mcp"
DEFAULT_SYSTEM = (
    "You are a helpful assistant with access to the Folio internal knowledge base. "
    "When the user asks about documentation, always use the available tools. "
    "Recommended flow: 1) list_topics to discover vocabulary, "
    "2) search_docs with exact terms, 3) get_document to read full content."
)


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
