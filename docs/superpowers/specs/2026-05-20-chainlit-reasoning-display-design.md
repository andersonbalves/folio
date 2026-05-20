# Chainlit Reasoning Display

**Date:** 2026-05-20
**Status:** Approved
**Scope:** `scripts/web_chat.py` only

## Problem

`make chat-web` shows MCP tool calls via `cl.Step` but never displays model reasoning. Gemini 2.5 Pro (the default model) produces two kinds of reasoning content that go unused:

1. `reasoning_content` — thinking tokens the model emits before its response
2. Pre-tool-call text — `assistant_message.content` when `tool_calls` is also present

The CLI (`chat.py`) exposes this via `DebugPrinter.thinking()` with `--debug`. The web UI has no equivalent.

## Design

### Approach

Two separate collapsible `cl.Step` blocks per LLM iteration, one for each reasoning type. Tool call steps remain unchanged.

Visual structure per user message:

```
[user message]
  🧠 Reasoning   ← collapsed  (reasoning_content from model)
  💭 Thinking    ← collapsed  (assistant text when tool_calls present)
  [tool: list_topics]
  [tool: search_docs]
[assistant] final response
```

Steps only appear when their content is non-empty. A response with no reasoning produces no extra steps.

### Env Var

`LLM_THINKING_BUDGET` — integer, default `0` (disabled).

- `0` or unset: thinking param omitted from litellm call entirely (safe for models that reject it)
- `> 0`: passes `thinking={"type": "enabled", "budget_tokens": N}` to litellm

Invalid (non-numeric) value raises `ValueError` at startup, not at request time.

### Implementation

All changes in `_handle_message` and the litellm call site in `scripts/web_chat.py`.

**Thinking budget (litellm call):**

```python
extras: dict = {}
budget = int(os.environ.get("LLM_THINKING_BUDGET", "0"))
if budget > 0:
    extras["thinking"] = {"type": "enabled", "budget_tokens": budget}

response = await litellm.acompletion(
    model=LLM_MODEL,
    messages=messages,
    tools=openai_tools or None,
    **extras,
)
```

**Reasoning content step:**

```python
reasoning = getattr(assistant_message, "reasoning_content", None)
if reasoning:
    async with cl.Step(name="🧠 Reasoning") as step:
        step.output = reasoning
```

**Pre-tool-call thinking step:**

```python
if assistant_message.content and assistant_message.tool_calls:
    async with cl.Step(name="💭 Thinking") as step:
        step.output = assistant_message.content
```

Both blocks execute before the existing tool-call loop. Order within each iteration:

1. Show `🧠 Reasoning` (if `reasoning_content` present)
2. Show `💭 Thinking` (if content + tool_calls)
3. Existing: append assistant message to history, send `cl.Message` if no tool calls
4. Existing: iterate tool calls via `cl.Step`

### Error Handling

- Missing `reasoning_content`: `getattr(..., None)` — no step, no error
- Model doesn't support thinking budget: omit param (budget = 0)
- Invalid `LLM_THINKING_BUDGET`: crash at boot with clear `ValueError`

### Testing

No new automated tests. Reasoning extraction is a one-liner conditional with no branching logic worth unit-testing. The litellm + Chainlit path has no test harness in this project.

## Out of Scope

- Toggle UI button for reasoning visibility
- Fixed thinking budget in code
- Changes to `chat.py` (CLI already has `--debug`)
- Changes to any file outside `scripts/web_chat.py`
