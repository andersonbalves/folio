# Design: Ollama MCP Chat Script

**Date:** 2026-05-19
**Status:** Approved

## Overview

Single-file dev tool (`scripts/chat.py`) providing a conversational REPL where a local Ollama model autonomously uses the `folio-mcp` MCP server tools to answer questions about indexed documentation.

## Goals

- Test `folio-mcp` end-to-end via real MCP stdio transport
- Conversational interface with full message history across turns
- Zero changes to existing packages or pyproject.toml files

## Non-Goals

- Production use or deployment
- Manual tool invocation (model decides autonomously)
- New uv workspace package

## Architecture

```
scripts/chat.py  (PEP 723 inline deps)
│
├── MCPBridge
│   ├── Spawns folio-mcp via FastMCP stdio Client
│   ├── list_tools() → list of MCP tool schemas
│   └── call_tool(name, args) → str result
│
├── OllamaAgent
│   ├── Converts MCP schemas → Ollama tool format (OpenAI-compatible)
│   ├── Maintains message history (full conversation)
│   └── run(user_msg) → str (runs agent loop until final answer)
│
└── main()
    ├── argparse CLI
    └── readline REPL
```

## Dependencies (PEP 723 inline)

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["ollama", "fastmcp>=3.3.1"]
# ///
```

Run via: `uv run scripts/chat.py`

## CLI Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `qwen3:8b` | Ollama model name |
| `--mcp-command` | `uv run folio-mcp` | Command to spawn MCP server |
| `--system` | built-in | Override system prompt |

## Data Flow

### Startup

1. Parse CLI args
2. `MCPBridge` connects: spawns `folio-mcp` via FastMCP stdio transport
3. Fetch tool schemas from MCP server
4. Convert schemas to Ollama tool format
5. Print model name + available tools
6. Enter REPL

### Agent Loop (per turn)

```
user input
  → append {"role": "user", "content": input}
  → ollama.chat(model, history, tools)
  → has tool_calls?
      YES → for each tool call:
              display: [tool: <name>(<args>)]
              result = MCPBridge.call_tool(name, args)
              display truncated result (500 chars)
              append {"role": "tool", "content": result}
            → ollama.chat(model, history)  # final answer pass
      NO  → response is final answer
  → append assistant message to history
  → print final response
```

### Shutdown

- `Ctrl+C` or `Ctrl+D` → clean exit, FastMCP client context manager exits properly
- `/exit` command → same

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Ollama not running | `ConnectionRefusedError` caught at startup → message + exit(1) |
| `folio-mcp` fails to start | FastMCP raises → caught → message + exit(1) |
| Tool call fails | Error string injected as tool result → model handles gracefully |
| Model not found in Ollama | `ollama` lib raises → caught → message + exit(1) |

## UX Details

- Tool calls printed inline: `[tool: search_docs("kubernetes pods")]`
- Tool results truncated to 500 chars in display; full result sent to model
- `/help` prints available MCP tools and their descriptions
- `/exit` exits cleanly
- System prompt instructs model to use tools proactively for folio knowledge base queries

## Recommended Model

**Default:** `qwen3:8b` — most reliable tool calling, ~6GB VRAM, fits RTX 4070 laptop (8GB).
**Alternative:** `llama3.1:8b` — faster inference, slightly less stable tool calling.

## File Location

```
scripts/
  chat.py     ← new file
```

No other files created or modified.
