# /// script
# requires-python = ">=3.14"
# dependencies = ["ollama", "fastmcp>=3.3.1"]
# ///
"""Conversational REPL: Ollama model + folio-mcp tools via MCP stdio."""

from __future__ import annotations

import argparse
import asyncio
import json
import shlex
import sys
from pathlib import Path
from typing import Any

import mcp.types
import ollama
from fastmcp import Client
from fastmcp.client.client import CallToolResult

_RESET = "\033[0m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_DIM = "\033[2m"


class DebugPrinter:
    """Prints color-coded agent debug output. All methods are no-ops when disabled."""

    def __init__(self, enabled: bool) -> None:
        """Store whether debug output is enabled."""
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """Return True if debug output is enabled."""
        return self._enabled

    def thinking(self, text: str) -> None:
        """Print model reasoning text, if enabled."""
        if not self._enabled:
            return
        print(f"\n{_YELLOW}[thinking]{_RESET} {text}\n")  # noqa: T201

    def request(self, name: str, args: dict[str, Any]) -> None:
        """Print a tool request with its arguments as JSON, if enabled."""
        if not self._enabled:
            return
        print(f"{_CYAN}→ REQUEST{_RESET} {name}({json.dumps(args, ensure_ascii=False)})")  # noqa: T201

    def response(self, name: str, text: str) -> None:
        """Print a tool response with character count, if enabled."""
        if not self._enabled:
            return
        print(f"{_GREEN}← RESPONSE{_RESET} {name} {_DIM}({len(text)} chars){_RESET}\n{text}\n")  # noqa: T201


_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


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


DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_MCP_COMMAND = "uv run folio-mcp"
DEFAULT_SYSTEM = (
    "You are a helpful assistant. Use the available tools when they would help answer the question."
)


class OllamaAgent:
    """Drives the Ollama tool-calling agent loop with persistent message history."""

    def __init__(
        self,
        model: str,
        bridge: MCPBridge,
        tools: list[mcp.types.Tool],
        system: str = DEFAULT_SYSTEM,
        printer: DebugPrinter | None = None,
    ) -> None:
        """Initialise with model, bridge, tools, optional system prompt and debug printer."""
        self._model = model
        self._bridge = bridge
        self._ollama_tools = [mcp_tool_to_ollama(t) for t in tools]
        self._messages: list[Any] = [{"role": "system", "content": system}]
        self._printer = printer if printer is not None else DebugPrinter(enabled=False)

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
            assistant_msg = response.message  # type: ignore[union-attr]  # ty: ignore[unresolved-attribute]
            self._messages.append(assistant_msg)

            if not assistant_msg.tool_calls:
                return assistant_msg.content or ""

            if assistant_msg.content:
                self._printer.thinking(assistant_msg.content)

            for tool_call in assistant_msg.tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments or {}
                if self._printer.enabled:
                    self._printer.request(name, args)
                else:
                    print(f"  [tool: {name}({args})]")  # noqa: T201
                result_text = await self._bridge.call_tool(name, args)
                if self._printer.enabled:
                    self._printer.response(name, result_text)
                else:
                    truncated = result_text[:500] + "…" if len(result_text) > 500 else result_text
                    print(f"  → {truncated}")  # noqa: T201
                self._messages.append({"role": "tool", "content": result_text})


async def repl(agent: OllamaAgent, tools: list[mcp.types.Tool]) -> None:
    """Run the interactive input loop."""
    tool_names = [t.name for t in tools]
    print(f"\nTools: {', '.join(tool_names)}")  # noqa: T201
    print("Type /help for commands, /exit or Ctrl+D to quit.\n")  # noqa: T201

    while True:
        try:
            user_input = await asyncio.to_thread(input, "You: ")
        except EOFError:
            print("\nBye.")  # noqa: T201
            break

        user_input = user_input.strip()
        if not user_input:
            continue
        if user_input == "/exit":
            print("Bye.")  # noqa: T201
            break
        if user_input == "/help":
            print("Commands: /exit, /help")  # noqa: T201
            print("Available MCP tools:")  # noqa: T201
            for t in tools:
                print(f"  {t.name}: {t.description or '(no description)'}")  # noqa: T201
            continue

        try:
            response = await agent.run(user_input)
            print(f"\nAssistant: {response}\n")  # noqa: T201
        except ollama.ResponseError as exc:
            print(f"Ollama error: {exc}", file=sys.stderr)  # noqa: T201
        except KeyboardInterrupt:
            print("\nInterrupted. Continue or /exit.")  # noqa: T201


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Chat with folio docs via Ollama + MCP")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model (default: qwen3.5:9b)")
    parser.add_argument(
        "--mcp-command", default=DEFAULT_MCP_COMMAND, help="Command to spawn MCP server"
    )
    parser.add_argument("--system", default=DEFAULT_SYSTEM, help="System prompt override")
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Print full MCP request/response and model reasoning with color",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    asyncio.run(main_async(args))


async def main_async(args: argparse.Namespace) -> None:
    """Run the chat REPL."""
    parts = shlex.split(args.mcp_command)
    mcp_config = {
        "mcpServers": {
            "folio": {
                "command": parts[0],
                "args": parts[1:],
                "cwd": str(_PROJECT_ROOT),
            }
        }
    }

    print(f"Model: {args.model}")  # noqa: T201
    print("Connecting to folio-mcp…", end=" ", flush=True)  # noqa: T201

    try:
        async with Client(mcp_config) as client:
            print("connected.")  # noqa: T201
            bridge = MCPBridge(client)
            tools = await bridge.list_tools()
            printer = DebugPrinter(enabled=args.debug)
            agent = OllamaAgent(args.model, bridge, tools, system=args.system, printer=printer)
            await repl(agent, tools)
    except ConnectionRefusedError:
        print("\nOllama not running. Start with: ollama serve", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    except Exception as exc:
        if "folio-mcp" in str(exc) or "mcp" in str(exc).lower():
            print(f"\nFailed to start folio-mcp: {exc}", file=sys.stderr)  # noqa: T201
        else:
            print(f"\nError: {exc}", file=sys.stderr)  # noqa: T201
        sys.exit(1)


if __name__ == "__main__":
    main()
