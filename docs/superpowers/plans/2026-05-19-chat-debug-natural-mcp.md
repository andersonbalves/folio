# Chat Debug Mode & Natural MCP Usage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--debug` flag to `scripts/chat.py` that surfaces the Ollama agent's reasoning and full MCP request/response with color-coded output; replace the prescriptive system prompt with a minimal persona that lets the model discover tool usage autonomously.

**Architecture:** Add `DebugPrinter` class (no-op when disabled, colored output when enabled) and thread it through `OllamaAgent`. Three public methods: `thinking()`, `request()`, `response()`. Non-debug display unchanged. `DEFAULT_SYSTEM` becomes one sentence.

**Tech Stack:** Python 3.14, stdlib only (`json`, ANSI escape codes). Tests extend `packages/mcp-server/tests/test_chat_helpers.py` via `importlib` loader already in place.

---

## File Structure

| File | Change |
|---|---|
| `scripts/chat.py` | Add `import json`, add `DebugPrinter`, update `OllamaAgent.__init__` + `run()`, update `DEFAULT_SYSTEM`, add `--debug` to argparse, update `main_async()` |
| `packages/mcp-server/tests/test_chat_helpers.py` | Add `TestDebugPrinter`, `TestOllamaAgentDebug`, `TestCLI` test classes |

---

### Task 1: Add `DebugPrinter` class

**Files:**
- Modify: `scripts/chat.py` — add `import json` and `DebugPrinter`
- Modify: `packages/mcp-server/tests/test_chat_helpers.py` — add `TestDebugPrinter`

- [ ] **Step 1: Write failing tests for `DebugPrinter`**

Add to `packages/mcp-server/tests/test_chat_helpers.py`, after the existing imports block (after line 22 where `extract_result_text` is assigned):

```python
DebugPrinter = _mod.DebugPrinter
```

Add this class at the bottom of the file:

```python
class TestDebugPrinter:
    def test_disabled_thinking_produces_no_output(self, capsys):
        printer = DebugPrinter(enabled=False)
        printer.thinking("some reasoning")
        assert capsys.readouterr().out == ""

    def test_disabled_request_produces_no_output(self, capsys):
        printer = DebugPrinter(enabled=False)
        printer.request("search_docs", {"query": "k8s"})
        assert capsys.readouterr().out == ""

    def test_disabled_response_produces_no_output(self, capsys):
        printer = DebugPrinter(enabled=False)
        printer.response("search_docs", "some result")
        assert capsys.readouterr().out == ""

    def test_enabled_false_property(self):
        printer = DebugPrinter(enabled=False)
        assert printer.enabled is False

    def test_enabled_true_property(self):
        printer = DebugPrinter(enabled=True)
        assert printer.enabled is True

    def test_enabled_thinking_contains_text(self, capsys):
        printer = DebugPrinter(enabled=True)
        printer.thinking("Let me search that.")
        out = capsys.readouterr().out
        assert "thinking" in out
        assert "Let me search that." in out

    def test_enabled_request_contains_name_and_args_json(self, capsys):
        printer = DebugPrinter(enabled=True)
        printer.request("search_docs", {"query": "kubernetes"})
        out = capsys.readouterr().out
        assert "REQUEST" in out
        assert "search_docs" in out
        assert '"kubernetes"' in out

    def test_enabled_response_contains_name_and_text(self, capsys):
        printer = DebugPrinter(enabled=True)
        printer.response("search_docs", "Full result text here.")
        out = capsys.readouterr().out
        assert "RESPONSE" in out
        assert "Full result text here." in out

    def test_enabled_response_shows_char_count(self, capsys):
        printer = DebugPrinter(enabled=True)
        text = "x" * 42
        printer.response("tool", text)
        out = capsys.readouterr().out
        assert "42" in out
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd packages/mcp-server && uv run pytest tests/test_chat_helpers.py::TestDebugPrinter -v
```

Expected: `AttributeError: module 'chat' has no attribute 'DebugPrinter'`

- [ ] **Step 3: Add `import json` and `DebugPrinter` to `scripts/chat.py`**

Add `import json` to the stdlib imports block (after `import shlex`, before `import sys`).

Add these constants and class after the existing imports, before `_PROJECT_ROOT`:

```python
_RESET = "\033[0m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_DIM = "\033[2m"


class DebugPrinter:
    """Prints color-coded agent debug output. All methods are no-ops when disabled."""

    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def thinking(self, text: str) -> None:
        if not self._enabled:
            return
        print(f"\n{_YELLOW}[thinking]{_RESET} {text}\n")  # noqa: T201

    def request(self, name: str, args: dict[str, Any]) -> None:
        if not self._enabled:
            return
        print(f"{_CYAN}→ REQUEST{_RESET} {name}({json.dumps(args, ensure_ascii=False)})")  # noqa: T201

    def response(self, name: str, text: str) -> None:
        if not self._enabled:
            return
        print(f"{_GREEN}← RESPONSE{_RESET} {_DIM}({len(text)} chars){_RESET}\n{text}\n")  # noqa: T201
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd packages/mcp-server && uv run pytest tests/test_chat_helpers.py::TestDebugPrinter -v
```

Expected: 9 tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/chat.py packages/mcp-server/tests/test_chat_helpers.py
git commit -m "feat(scripts): add DebugPrinter for color-coded MCP debug output"
```

---

### Task 2: Update `OllamaAgent` to use `DebugPrinter`

**Files:**
- Modify: `scripts/chat.py` — update `OllamaAgent.__init__` signature and `run()` loop
- Modify: `packages/mcp-server/tests/test_chat_helpers.py` — add `TestOllamaAgentDebug`

- [ ] **Step 1: Write failing tests for updated `OllamaAgent`**

Add to the test file, after the `DebugPrinter = _mod.DebugPrinter` line:

```python
OllamaAgent = _mod.OllamaAgent
```

Add this class at the bottom of the file:

```python
class TestOllamaAgentDebug:
    def _make_response(self, content: str | None, tool_calls=None):
        msg = MagicMock()
        msg.content = content
        msg.tool_calls = tool_calls
        resp = MagicMock()
        resp.message = msg
        return resp

    def test_accepts_printer_parameter(self):
        bridge = MagicMock()
        printer = DebugPrinter(enabled=False)
        agent = OllamaAgent("model", bridge, [], printer=printer)
        assert agent._printer is printer

    def test_none_printer_defaults_to_disabled(self):
        bridge = MagicMock()
        agent = OllamaAgent("model", bridge, [])
        assert isinstance(agent._printer, DebugPrinter)
        assert agent._printer.enabled is False

    def test_thinking_called_when_content_before_tool_calls(self):
        import asyncio
        from unittest.mock import AsyncMock, patch

        bridge = MagicMock()
        bridge.call_tool = AsyncMock(return_value="tool result")
        mock_printer = MagicMock()
        mock_printer.enabled = True

        tool_call = MagicMock()
        tool_call.function.name = "search_docs"
        tool_call.function.arguments = {"query": "k8s"}

        responses = iter([
            self._make_response("Let me look that up.", [tool_call]),
            self._make_response("Here is the answer.", None),
        ])

        async def fake_to_thread(fn, **kwargs):
            return next(responses)

        agent = OllamaAgent("model", bridge, [], printer=mock_printer)
        with patch("asyncio.to_thread", side_effect=fake_to_thread):
            asyncio.run(agent.run("find k8s docs"))

        mock_printer.thinking.assert_called_once_with("Let me look that up.")
        mock_printer.request.assert_called_once_with("search_docs", {"query": "k8s"})
        mock_printer.response.assert_called_once_with("search_docs", "tool result")

    def test_thinking_not_called_when_no_content(self):
        import asyncio
        from unittest.mock import AsyncMock, patch

        bridge = MagicMock()
        bridge.call_tool = AsyncMock(return_value="result")
        mock_printer = MagicMock()
        mock_printer.enabled = True

        tool_call = MagicMock()
        tool_call.function.name = "list_topics"
        tool_call.function.arguments = {}

        responses = iter([
            self._make_response(None, [tool_call]),
            self._make_response("Done.", None),
        ])

        async def fake_to_thread(fn, **kwargs):
            return next(responses)

        agent = OllamaAgent("model", bridge, [], printer=mock_printer)
        with patch("asyncio.to_thread", side_effect=fake_to_thread):
            asyncio.run(agent.run("list topics"))

        mock_printer.thinking.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd packages/mcp-server && uv run pytest tests/test_chat_helpers.py::TestOllamaAgentDebug -v
```

Expected: `TypeError` — `OllamaAgent.__init__()` got unexpected keyword argument `printer`.

- [ ] **Step 3: Update `OllamaAgent.__init__` and `run()` in `scripts/chat.py`**

Update the `__init__` signature:

```python
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
```

Replace the `for tool_call in assistant_msg.tool_calls:` block in `run()` with:

```python
            if assistant_msg.content:
                self._printer.thinking(assistant_msg.content)

            for tool_call in assistant_msg.tool_calls:
                name = tool_call.function.name
                args = tool_call.function.arguments or {}
                if not self._printer.enabled:
                    print(f"  [tool: {name}({args})]")  # noqa: T201
                self._printer.request(name, args)
                result_text = await self._bridge.call_tool(name, args)
                if not self._printer.enabled:
                    truncated = result_text[:500] + "…" if len(result_text) > 500 else result_text
                    print(f"  → {truncated}")  # noqa: T201
                self._printer.response(name, result_text)
                self._messages.append({"role": "tool", "content": result_text})
```

- [ ] **Step 4: Run all chat helper tests to verify they pass**

```bash
cd packages/mcp-server && uv run pytest tests/test_chat_helpers.py -v
```

Expected: all tests pass (original 7 + new `TestOllamaAgentDebug` tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/chat.py packages/mcp-server/tests/test_chat_helpers.py
git commit -m "feat(scripts): thread DebugPrinter through OllamaAgent"
```

---

### Task 3: Minimal system prompt + `--debug` CLI flag

**Files:**
- Modify: `scripts/chat.py` — update `DEFAULT_SYSTEM`, add `--debug` to `parse_args()`, update `main_async()`
- Modify: `packages/mcp-server/tests/test_chat_helpers.py` — add `TestCLI`

- [ ] **Step 1: Write failing tests**

Add this class at the bottom of the test file:

```python
class TestCLI:
    def test_default_system_is_minimal(self):
        assert "always use" not in _mod.DEFAULT_SYSTEM
        assert "Recommended flow" not in _mod.DEFAULT_SYSTEM
        assert "helpful assistant" in _mod.DEFAULT_SYSTEM

    def test_debug_flag_defaults_to_false(self):
        import sys
        old = sys.argv
        sys.argv = ["chat.py"]
        args = _mod.parse_args()
        sys.argv = old
        assert args.debug is False

    def test_debug_flag_set_true(self):
        import sys
        old = sys.argv
        sys.argv = ["chat.py", "--debug"]
        args = _mod.parse_args()
        sys.argv = old
        assert args.debug is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd packages/mcp-server && uv run pytest tests/test_chat_helpers.py::TestCLI -v
```

Expected: `test_default_system_is_minimal` fails (`"always use"` present in current prompt), `test_debug_flag_*` fail with `AttributeError` (no `debug` attr on `Namespace`).

- [ ] **Step 3: Update `DEFAULT_SYSTEM`, `parse_args()`, and `main_async()` in `scripts/chat.py`**

Replace `DEFAULT_SYSTEM`:

```python
DEFAULT_SYSTEM = "You are a helpful assistant. Use the available tools when they would help answer the question."
```

Add `--debug` to `parse_args()` (after the `--system` argument):

```python
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Print full MCP request/response and model reasoning with color",
    )
```

In `main_async()`, after the `tools = await bridge.list_tools()` line, construct the printer and pass it to `OllamaAgent`:

```python
            printer = DebugPrinter(enabled=args.debug)
            agent = OllamaAgent(args.model, bridge, tools, system=args.system, printer=printer)
```

Remove the now-unused standalone `OllamaAgent(args.model, bridge, tools, system=args.system)` line.

- [ ] **Step 4: Run all chat helper tests to verify they pass**

```bash
cd packages/mcp-server && uv run pytest tests/test_chat_helpers.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/chat.py packages/mcp-server/tests/test_chat_helpers.py
git commit -m "feat(scripts): add --debug flag and minimal system prompt to chat REPL"
```

---

## Self-Review

**Spec coverage:**
- `DebugPrinter` with `thinking()`, `request()`, `response()` → Task 1 ✓
- `enabled` property for conditional non-debug display → Task 1 ✓
- `OllamaAgent` receives `printer: DebugPrinter | None = None` → Task 2 ✓
- `thinking()` called when `assistant_msg.content` non-empty and tool_calls present → Task 2 ✓
- `request()` before `call_tool`, `response()` after → Task 2 ✓
- Non-debug display unchanged when printer disabled → Task 2 ✓
- `DEFAULT_SYSTEM` minimal → Task 3 ✓
- `--debug` flag → Task 3 ✓
- `main_async()` constructs `DebugPrinter(enabled=args.debug)` → Task 3 ✓

**No placeholders:** All steps contain actual code.

**Type consistency:**
- `DebugPrinter` defined Task 1, referenced in Task 2 and 3 — consistent.
- `printer.enabled` property defined Task 1, used in Task 2 — consistent.
- `OllamaAgent(... printer=printer)` — keyword matches new `__init__` signature.
