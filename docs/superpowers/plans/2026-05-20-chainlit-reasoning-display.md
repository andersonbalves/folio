# Chainlit Reasoning Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show model reasoning (thinking tokens + pre-tool-call text) as collapsible `cl.Step` blocks in the Chainlit web UI.

**Architecture:** Add `LLM_THINKING_BUDGET` env var; inject thinking param into litellm when set; extract `reasoning_content` and pre-tool-call text from each LLM response; render each as a separate `cl.Step` before tool-call steps.

**Tech Stack:** Chainlit (`cl.Step`), litellm (`acompletion`), Python 3.14

---

### Task 1: Add thinking budget env var and update litellm call

**Files:**
- Modify: `scripts/web_chat.py:37-39` (module-level constants)
- Modify: `scripts/web_chat.py:135-139` (litellm call inside `_handle_message`)

No automated tests exist for this path. Verification is manual (Task 3).

- [ ] **Step 1: Add `LLM_THINKING_BUDGET` constant and `_THINKING_EXTRAS` dict after line 39**

Replace the module-level constants block (lines 37–39):

```python
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini/gemini-2.5-pro")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant.")
MCP_LAMBDA_URL = os.environ.get("MCP_LAMBDA_URL")
```

With:

```python
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini/gemini-2.5-pro")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant.")
MCP_LAMBDA_URL = os.environ.get("MCP_LAMBDA_URL")
LLM_THINKING_BUDGET = int(os.environ.get("LLM_THINKING_BUDGET", "0"))
_THINKING_EXTRAS: dict = (
    {"thinking": {"type": "enabled", "budget_tokens": LLM_THINKING_BUDGET}}
    if LLM_THINKING_BUDGET > 0
    else {}
)
```

`int(...)` raises `ValueError` on non-numeric values at import time — intentional early failure.

- [ ] **Step 2: Update litellm call to pass `_THINKING_EXTRAS`**

Replace lines 135–139:

```python
        response = await litellm.acompletion(
            model=LLM_MODEL,
            messages=messages,
            tools=openai_tools if openai_tools else None,
        )
```

With:

```python
        response = await litellm.acompletion(
            model=LLM_MODEL,
            messages=messages,
            tools=openai_tools if openai_tools else None,
            **_THINKING_EXTRAS,
        )
```

---

### Task 2: Restructure `_handle_message` to show reasoning steps

**Files:**
- Modify: `scripts/web_chat.py:141-186` (assistant message handling inside the loop)

This task also fixes an existing bug: when both `content` and `tool_calls` are present, the old code appended content to `messages` twice (once as `{"role": "assistant", "content": ...}` and once via `model_dump`). The new structure appends only via `model_dump` when tool calls are present.

- [ ] **Step 1: Replace lines 141–186 with the restructured handler**

The current block to replace (lines 141–186):

```python
        assistant_message = response.choices[0].message

        if assistant_message.content:
            messages.append({"role": "assistant", "content": assistant_message.content})
            await cl.Message(content=assistant_message.content).send()

        if assistant_message.tool_calls:
            # Append the assistant's tool call message to history
            messages.append(assistant_message.model_dump(exclude_unset=True))

            for tool_call in assistant_message.tool_calls:
                name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                async with cl.Step(name=name) as step:
                    step.input = arguments

                    try:
                        result = await session.call_tool(name, arguments)

                        result_text = "\n".join(
                            [b.text for b in result.content if hasattr(b, "text")]
                        )
                        step.output = result_text

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": name,
                                "content": result_text,
                            }
                        )
                    except Exception as e:
                        error_msg = f"Error calling tool {name}: {str(e)}"
                        step.output = error_msg
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": name,
                                "content": error_msg,
                            }
                        )
        else:
            break
```

Replace with:

```python
        assistant_message = response.choices[0].message

        reasoning = getattr(assistant_message, "reasoning_content", None)
        if reasoning:
            async with cl.Step(name="🧠 Reasoning") as step:
                step.output = reasoning

        if assistant_message.tool_calls:
            if assistant_message.content:
                async with cl.Step(name="💭 Thinking") as step:
                    step.output = assistant_message.content

            messages.append(assistant_message.model_dump(exclude_unset=True))

            for tool_call in assistant_message.tool_calls:
                name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                async with cl.Step(name=name) as step:
                    step.input = arguments

                    try:
                        result = await session.call_tool(name, arguments)

                        result_text = "\n".join(
                            [b.text for b in result.content if hasattr(b, "text")]
                        )
                        step.output = result_text

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": name,
                                "content": result_text,
                            }
                        )
                    except Exception as e:
                        error_msg = f"Error calling tool {name}: {str(e)}"
                        step.output = error_msg
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": name,
                                "content": error_msg,
                            }
                        )
        else:
            if assistant_message.content:
                messages.append({"role": "assistant", "content": assistant_message.content})
                await cl.Message(content=assistant_message.content).send()
            break
```

---

### Task 3: Smoke test and commit

**Files:**
- No file changes

- [ ] **Step 1: Run lint + typecheck**

```bash
make check
```

Expected: no errors. If `ruff` reports import order or line-length issues in `web_chat.py`, run `make lint --fix` (or `ruff check --fix scripts/web_chat.py`) and re-check.

- [ ] **Step 2: Start the stack and web UI**

```bash
make up
# in another terminal:
make chat-web
```

Open the Chainlit URL printed in the terminal (usually `http://localhost:8000`).

- [ ] **Step 3: Send a message that triggers tool use**

Example: `"What topics are available in the knowledge base?"`

Expected UI output:
- `🧠 Reasoning` step appears (collapsed) if `LLM_THINKING_BUDGET > 0` and model returns thinking tokens
- `💭 Thinking` step appears (collapsed) if model produces text before calling a tool
- Tool call steps (`list_topics`, etc.) appear as before
- Final assistant message appears

Without `LLM_THINKING_BUDGET` set, `🧠 Reasoning` may not appear (model may not emit thinking tokens by default). Set `LLM_THINKING_BUDGET=8192` in `.env` to verify that path.

- [ ] **Step 4: Commit**

```bash
git add scripts/web_chat.py
git commit -m "feat(chat-web): show reasoning and thinking steps in Chainlit UI"
```
