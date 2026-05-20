# Design: Chat Debug Mode & Natural MCP Usage

**Date:** 2026-05-19
**Status:** Approved
**Evolves:** `2026-05-19-ollama-mcp-chat-design.md`

## Overview

Two focused improvements to `scripts/chat.py`:

1. **Natural MCP usage** — replace prescriptive system prompt with minimal persona; let MCP tool schemas guide the model autonomously, matching how production coding agents (Claude Code, Copilot, Cursor) behave.
2. **Debug visibility** — `--debug` flag surfaces the agent's full reasoning: assistant text before tool calls, complete MCP request/response with color-coded output.

## Goals

- Emulate real agent behavior: model discovers when/how to call tools from schema descriptions, not from prompt directives
- Make the agent loop transparent for learning/debugging purposes
- Zero new dependencies

## Non-Goals

- Persistent debug log to file
- Structured logging (JSON, etc.)
- Changing MCP tool descriptions in `folio-mcp`

## Architecture

```
scripts/chat.py
│
├── DebugPrinter           ← NEW
│   ├── enabled: bool
│   ├── thinking(text)     → yellow, assistant text before tool calls
│   ├── request(name, args) → cyan, full args as JSON
│   └── response(name, text) → green, full response, no truncation
│
├── OllamaAgent            ← MODIFIED
│   ├── Constructor receives printer: DebugPrinter
│   └── run() emits debug events at each agent loop step
│
└── DEFAULT_SYSTEM         ← MODIFIED
    └── Minimal persona, no prescribed tool flow
```

## `DebugPrinter`

Single-responsibility class for debug output. All methods are no-ops when `enabled=False`.

```python
_RESET  = "\033[0m"
_YELLOW = "\033[33m"   # assistant thinking
_CYAN   = "\033[36m"   # mcp request
_GREEN  = "\033[32m"   # mcp response
_DIM    = "\033[2m"

class DebugPrinter:
    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled

    def thinking(self, text: str) -> None:
        if not self._enabled:
            return
        print(f"\n{_YELLOW}[thinking]{_RESET} {text}\n")

    def request(self, name: str, args: dict[str, Any]) -> None:
        if not self._enabled:
            return
        print(f"{_CYAN}→ REQUEST{_RESET} {name}({json.dumps(args, ensure_ascii=False)})")

    def response(self, name: str, text: str) -> None:
        if not self._enabled:
            return
        print(f"{_GREEN}← RESPONSE{_RESET} {_DIM}({len(text)} chars){_RESET}\n{text}\n")
```

No new imports beyond `json` (stdlib).

## `OllamaAgent` Changes

Constructor signature:

```python
def __init__(
    self,
    model: str,
    bridge: MCPBridge,
    tools: list[mcp.types.Tool],
    system: str = DEFAULT_SYSTEM,
    printer: DebugPrinter | None = None,  # None → DebugPrinter(enabled=False) constructed inside
) -> None:
```

`run()` loop — debug events:

| Event | When | Method |
|---|---|---|
| Assistant thinking | `assistant_msg.content` is non-empty and tool_calls present | `printer.thinking(content)` |
| MCP request | Before each `bridge.call_tool()` | `printer.request(name, args)` |
| MCP response | After each `bridge.call_tool()` | `printer.response(name, result_text)` |

Non-debug display is unchanged: `[tool: name(args)]` + truncated 500-char result.

## System Prompt Change

**Before (prescriptive):**
```
"You are a helpful assistant with access to the Folio internal knowledge base.
When the user asks about documentation, always use the available tools.
Recommended flow: 1) list_topics to discover vocabulary, 2) search_docs with exact terms,
3) get_document to read full content."
```

**After (minimal):**
```
"You are a helpful assistant. Use the available tools when they would help answer the question."
```

Rationale: production agents like Claude Code do not prescribe tool call order in the system prompt. The model infers when and how to use tools from the tool schema `description` fields. Prescribing a flow interferes with this natural discovery and produces rigid, non-adaptive behavior.

## CLI

`--debug` flag added to argparse (`store_true`, default `False`):

```
uv run scripts/chat.py --debug
```

`main_async()` constructs `DebugPrinter(enabled=args.debug)` and passes it to `OllamaAgent`.

## Data Flow (debug mode)

```
user input
  → ollama.chat(model, history, tools)
  → assistant has tool_calls?
      YES → if content non-empty:
              printer.thinking(content)          ← yellow
            for each tool call:
              printer.request(name, args)        ← cyan
              result = bridge.call_tool(name, args)
              printer.response(name, result)     ← green
              append tool result to history
            → ollama.chat(model, history)        ← final answer
      NO  → response is final answer
  → print final response
```

## Error Handling

No changes to existing error handling.

## Files Changed

| File | Change |
|---|---|
| `scripts/chat.py` | Add `DebugPrinter`, update `OllamaAgent`, update `DEFAULT_SYSTEM`, add `--debug` flag |

No other files modified.
