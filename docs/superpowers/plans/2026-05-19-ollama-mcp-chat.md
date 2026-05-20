# Ollama MCP Chat Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `scripts/chat.py` — a conversational REPL where a local Ollama model autonomously uses the `folio-mcp` MCP server tools to answer questions about indexed documentation.

**Architecture:** Single Python file with PEP 723 inline deps. `MCPBridge` wraps a FastMCP `Client` connected via stdio to a spawned `folio-mcp` process. `OllamaAgent` maintains message history and drives the tool-calling agent loop. A simple async REPL wires them together.

**Tech Stack:** Python 3.14, `ollama` (Python SDK), `fastmcp>=3.3.1` (already in workspace), `mcp.types`, `asyncio`, `readline`, `argparse`, `shlex`

---

## File Structure

| Path                                             | Action | Responsibility                                            |
| ------------------------------------------------ | ------ | --------------------------------------------------------- |
| `scripts/chat.py`                                | Create | Entire script — inline deps, helpers, classes, REPL, main |
| `packages/mcp-server/tests/test_chat_helpers.py` | Create | Unit tests for pure helper functions                      |

---

### Task 1: Scaffold the script

**Files:**

- Create: `scripts/chat.py`

- [ ] **Step 1: Create `scripts/chat.py` with skeleton**

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["ollama", "fastmcp>=3.3.1"]
# ///
"""Conversational REPL: Ollama model + folio-mcp tools via MCP stdio."""

from __future__ import annotations

import argparse
import asyncio
import shlex
import sys
from pathlib import Path

import mcp.types
import ollama
from fastmcp import Client
from fastmcp.client.client import CallToolResult

_PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_MCP_COMMAND = "uv run folio-mcp"
DEFAULT_SYSTEM = (
    "You are a helpful assistant with access to the Folio internal knowledge base. "
    "When the user asks about documentation, always use the available tools. "
    "Recommended flow: 1) list_topics to discover vocabulary, "
    "2) search_docs with exact terms, 3) get_document to read full content."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chat with folio docs via Ollama + MCP")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model (default: qwen2.5:7b)")
    parser.add_argument("--mcp-command", default=DEFAULT_MCP_COMMAND, help="Command to spawn MCP server")
    parser.add_argument("--system", default=DEFAULT_SYSTEM, help="System prompt override")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(main_async(args))


async def main_async(args: argparse.Namespace) -> None:
    print("TODO: implement")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify argparse works**

Run: `uv run scripts/chat.py --help`

Expected output contains:

```
usage: chat.py [-h] [--model MODEL] [--mcp-command MCP_COMMAND] [--system SYSTEM]
```

- [ ] **Step 3: Commit**

```bash
git add scripts/chat.py
git commit -m "feat(scripts): scaffold chat.py with argparse and PEP 723 deps"
```

---

### Task 2: Helper functions + tests

**Files:**

- Modify: `scripts/chat.py` (add helpers)
- Create: `packages/mcp-server/tests/test_chat_helpers.py`

- [ ] **Step 1: Write failing tests**

Create `packages/mcp-server/tests/test_chat_helpers.py`:

```python
"""Tests for pure helper functions in scripts/chat.py."""

import importlib.util
import sys
from pathlib import Path

import mcp.types
import pytest

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
        schema = {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
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
        from fastmcp.client.client import CallToolResult
        from unittest.mock import MagicMock

        non_text = MagicMock()
        non_text.type = "image"
        result = CallToolResult(
            content=[non_text, mcp.types.TextContent(type="text", text="actual text")],
            structured_content=None,
            meta=None,
        )
        assert extract_result_text(result) == "actual text"
```

- [ ] **Step 2: Run tests to confirm they fail**

Run: `pytest packages/mcp-server/tests/test_chat_helpers.py -v`

Expected: `AttributeError` — `mcp_tool_to_ollama` not defined yet.

- [ ] **Step 3: Add helper functions to `scripts/chat.py`**

Add after imports, before `_PROJECT_ROOT`:

```python
def mcp_tool_to_ollama(tool: mcp.types.Tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


def extract_result_text(result: CallToolResult) -> str:
    parts = [
        block.text
        for block in result.content
        if isinstance(block, mcp.types.TextContent)
    ]
    return "\n".join(parts) if parts else "(no text result)"
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `pytest packages/mcp-server/tests/test_chat_helpers.py -v`

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/chat.py packages/mcp-server/tests/test_chat_helpers.py
git commit -m "feat(scripts): add mcp_tool_to_ollama and extract_result_text helpers"
```

---

### Task 3: MCPBridge

**Files:**

- Modify: `scripts/chat.py` (add `MCPBridge` class)

- [ ] **Step 1: Add `MCPBridge` class to `scripts/chat.py`**

Add after the helper functions:

```python
class MCPBridge:
    """Wraps a connected FastMCP Client, exposing tool list/call operations."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list_tools(self) -> list[mcp.types.Tool]:
        return await self._client.list_tools()

    async def call_tool(self, name: str, arguments: dict) -> str:
        try:
            result = await self._client.call_tool(name, arguments, raise_on_error=False)
            return extract_result_text(result)
        except Exception as exc:
            return f"[tool error: {exc}]"
```

- [ ] **Step 2: Verify `MCPBridge` is importable**

Run: `uv run python -c "import importlib.util, pathlib; s=importlib.util.spec_from_file_location('c','scripts/chat.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.MCPBridge)"`

Expected: `<class 'chat.MCPBridge'>` (no errors).

- [ ] **Step 3: Commit**

```bash
git add scripts/chat.py
git commit -m "feat(scripts): add MCPBridge wrapping FastMCP Client"
```

---

### Task 4: OllamaAgent

**Files:**

- Modify: `scripts/chat.py` (add `OllamaAgent` class)

- [ ] **Step 1: Add `OllamaAgent` class to `scripts/chat.py`**

Add after `MCPBridge`:

```python
class OllamaAgent:
    """Drives the Ollama tool-calling agent loop with persistent message history."""

    def __init__(
        self,
        model: str,
        bridge: MCPBridge,
        tools: list[mcp.types.Tool],
        system: str = DEFAULT_SYSTEM,
    ) -> None:
        self._model = model
        self._bridge = bridge
        self._ollama_tools = [mcp_tool_to_ollama(t) for t in tools]
        self._messages: list = [{"role": "system", "content": system}]

    async def run(self, user_msg: str) -> str:
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
                print(f"  [tool: {name}({args})]")
                result_text = await self._bridge.call_tool(name, args)
                truncated = result_text[:500] + "…" if len(result_text) > 500 else result_text
                print(f"  → {truncated}")
                self._messages.append({"role": "tool", "content": result_text})
```

- [ ] **Step 2: Verify class is importable**

Run: `uv run python -c "import importlib.util; s=importlib.util.spec_from_file_location('c','scripts/chat.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.OllamaAgent)"`

Expected: `<class 'chat.OllamaAgent'>` (no errors).

- [ ] **Step 3: Commit**

```bash
git add scripts/chat.py
git commit -m "feat(scripts): add OllamaAgent with tool-calling loop"
```

---

### Task 5: REPL and main_async()

**Files:**

- Modify: `scripts/chat.py` (add `repl()`, update `main_async()`)

- [ ] **Step 1: Add `import readline` at top of imports**

In `scripts/chat.py`, add `import readline` to the import block (after `import shlex`). This silently enables command history via up-arrow in the REPL without any explicit calls.

```python
import readline  # noqa: F401 — enables readline history for input()
```

- [ ] **Step 2: Add `repl()` function and update `main_async()`**

Replace the existing `main_async` stub and add `repl()`:

```python
async def repl(agent: OllamaAgent, tools: list[mcp.types.Tool]) -> None:
    tool_names = [t.name for t in tools]
    print(f"\nTools: {', '.join(tool_names)}")
    print("Type /help for commands, /exit or Ctrl+D to quit.\n")

    while True:
        try:
            user_input = await asyncio.to_thread(input, "You: ")
        except EOFError:
            print("\nBye.")
            break

        user_input = user_input.strip()
        if not user_input:
            continue
        if user_input == "/exit":
            print("Bye.")
            break
        if user_input == "/help":
            print("Commands: /exit, /help")
            print("Available MCP tools:")
            for t in tools:
                print(f"  {t.name}: {t.description or '(no description)'}")
            continue

        try:
            response = await agent.run(user_input)
            print(f"\nAssistant: {response}\n")
        except ollama.ResponseError as exc:
            print(f"Ollama error: {exc}", file=sys.stderr)
        except KeyboardInterrupt:
            print("\nInterrupted. Continue or /exit.")


async def main_async(args: argparse.Namespace) -> None:
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

    print(f"Model: {args.model}")
    print("Connecting to folio-mcp…", end=" ", flush=True)

    try:
        async with Client(mcp_config) as client:
            print("connected.")
            bridge = MCPBridge(client)
            tools = await bridge.list_tools()
            agent = OllamaAgent(args.model, bridge, tools, system=args.system)
            await repl(agent, tools)
    except ConnectionRefusedError:
        print(f"\nOllama not running. Start with: ollama serve", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        if "folio-mcp" in str(exc) or "mcp" in str(exc).lower():
            print(f"\nFailed to start folio-mcp: {exc}", file=sys.stderr)
        else:
            print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 3: Verify `--help` still works**

Run: `uv run scripts/chat.py --help`

Expected: same help output as Task 1, Step 2.

- [ ] **Step 4: Commit**

```bash
git add scripts/chat.py
git commit -m "feat(scripts): add REPL loop and wire main_async with MCPBridge + OllamaAgent"
```

---

### Task 6: Smoke test and final commit

**Files:**

- None (testing only)

- [ ] **Step 1: Run full test suite**

Run: `pytest packages/mcp-server/tests/ -v`

Expected: all existing tests + 6 new `test_chat_helpers` tests PASS.

- [ ] **Step 2: Smoke test — infrastructure up**

Prerequisites: `make up && make migrate && make seed` (or `make k8s-docs`).

Run: `uv run scripts/chat.py --help`

Expected: help text with no import errors.

- [ ] **Step 3: Smoke test — Ollama running, folio-mcp reachable**

Prerequisites: `ollama serve` running, `ollama pull qwen2.5:7b` completed.

Run: `uv run scripts/chat.py`

Expected:

```
Model: qwen2.5:7b
Connecting to folio-mcp… connected.

Tools: list_topics, search_docs, get_document
Type /help for commands, /exit or Ctrl+D to quit.

You:
```

- [ ] **Step 4: Test a query that triggers tool use**

Type: `what topics are available?`

Expected: model calls `list_topics`, result is printed inline, model answers with topic list.

- [ ] **Step 5: Test `/help`**

Type: `/help`

Expected: prints commands and tool descriptions.

- [ ] **Step 6: Test `/exit`**

Type: `/exit`

Expected: prints `Bye.` and process exits cleanly.

- [ ] **Step 7: Final commit**

```bash
git add scripts/chat.py packages/mcp-server/tests/test_chat_helpers.py
git commit -m "feat(scripts): ollama mcp chat REPL complete"
```

---

## Self-Review

**Spec coverage:**

- ✅ Conversational REPL with message history — `OllamaAgent._messages`
- ✅ MCP client via stdio — `Client(mcp_config)` with MCPConfig dict
- ✅ Ollama model default `qwen2.5:7b` — `DEFAULT_MODEL`
- ✅ PEP 723 inline deps — header in Task 1
- ✅ `--model`, `--mcp-command`, `--system` args — `parse_args()`
- ✅ Tool calls printed inline — `[tool: name(args)]` in `OllamaAgent.run()`
- ✅ Tool results truncated to 500 chars in display — `result_text[:500]`
- ✅ `/help` prints available tools — `repl()`
- ✅ `/exit` exits cleanly — `repl()`
- ✅ Ctrl+D exits cleanly — `EOFError` in `repl()`
- ✅ Error: Ollama not running — `ConnectionRefusedError` in `main_async()`
- ✅ Error: folio-mcp fails to start — generic `Exception` in `main_async()`
- ✅ Tool call error → inject as tool result — `raise_on_error=False` + except in `MCPBridge.call_tool()`
- ✅ System prompt instructs proactive tool use — `DEFAULT_SYSTEM`

**Type consistency:**

- `MCPBridge.__init__` takes `Client` ✅ — `main_async` passes `client` from `async with Client(...) as client`
- `OllamaAgent.__init__` takes `MCPBridge` ✅ — `main_async` passes `bridge`
- `repl()` takes `OllamaAgent, list[mcp.types.Tool]` ✅ — `main_async` passes `agent, tools`
- `extract_result_text` used in `MCPBridge.call_tool` ✅ — defined before `MCPBridge`
- `mcp_tool_to_ollama` used in `OllamaAgent.__init__` ✅ — defined before `OllamaAgent`
