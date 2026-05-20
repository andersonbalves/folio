"""Chainlit web chat interface using MCP and Localstack."""

import contextlib
import json
import os

import sniffio

# Monkey-patch sniffio to fix NoEventLoopError caused by nest_asyncio in Python 3.14
sniffio.current_async_library = lambda: "asyncio"

import asyncio

# Patch asyncio.current_task to work with nest_asyncio in Python 3.14
_c_current_task = asyncio.current_task


def _patched_current_task(loop=None):
    task = _c_current_task(loop)
    if task is not None:
        return task
    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return None
    return getattr(asyncio.tasks, "_current_tasks", {}).get(loop)


asyncio.current_task = _patched_current_task
asyncio.tasks.current_task = (
    _patched_current_task  # asyncio.timeouts uses tasks.current_task directly
)

from typing import Any

import chainlit as cl
import litellm
import mcp.types
from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

load_dotenv()

LLM_MODEL = os.environ.get("LLM_MODEL", "gemini/gemini-2.5-pro")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant.")
MCP_LAMBDA_URL = os.environ.get("MCP_LAMBDA_URL")
LLM_THINKING_BUDGET = int(os.environ.get("LLM_THINKING_BUDGET", "0"))
_THINKING_EXTRAS: dict[str, Any] = (
    {"thinking": {"type": "enabled", "budget_tokens": LLM_THINKING_BUDGET}}
    if LLM_THINKING_BUDGET > 0
    else {}
)


async def _run_mcp_session(
    url: str,
    ready: asyncio.Event,
    done: asyncio.Event,
    holder: dict,
) -> None:
    """Own the full MCP session lifecycle in a single task.

    anyio cancel scopes must enter and exit in the same asyncio task.
    Chainlit runs each callback in separate tasks, so we keep the connection
    alive here and signal readiness/teardown via events.
    """
    async with sse_client(url) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        holder["session"] = session
        ready.set()
        await done.wait()


def mcp_tool_to_openai(tool: mcp.types.Tool) -> dict:
    """Convert an MCP tool schema to OpenAI function format."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        },
    }


@cl.on_chat_start
async def on_chat_start():
    """Initialize MCP connection and fetch available tools."""
    if not MCP_LAMBDA_URL:
        await cl.Message(content="Error: MCP_LAMBDA_URL environment variable is not set.").send()
        return

    msg = cl.Message(content="Connecting to MCP Server...", author="System")
    await msg.send()

    ready: asyncio.Event = asyncio.Event()
    done: asyncio.Event = asyncio.Event()
    holder: dict = {}

    task = asyncio.create_task(_run_mcp_session(MCP_LAMBDA_URL, ready, done, holder))
    cl.user_session.set("mcp_done", done)
    cl.user_session.set("mcp_task", task)

    try:
        await asyncio.wait_for(ready.wait(), timeout=10)
        session: ClientSession = holder["session"]
        cl.user_session.set("mcp_session", session)

        tools_response = await session.list_tools()
        tools = tools_response.tools
        cl.user_session.set("mcp_tools", tools)

        cl.user_session.set("messages", [{"role": "system", "content": SYSTEM_PROMPT}])

        msg.content = f"Connected! Found {len(tools)} tools: {', '.join([t.name for t in tools])}"
        await msg.update()
    except Exception as e:
        done.set()
        msg.content = f"Failed to connect to MCP: {str(e)}"
        await msg.update()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages and execute LLM tool calls."""
    try:
        await _handle_message(message)
    except Exception as e:
        import traceback

        await cl.Message(content=f"Error: {e}\n```\n{traceback.format_exc()}\n```").send()


async def _handle_message(message: cl.Message) -> None:
    session: ClientSession = cl.user_session.get("mcp_session")
    if not session:
        await cl.Message(content="Not connected to MCP. Please check the logs.").send()
        return

    mcp_tools = cl.user_session.get("mcp_tools", [])
    openai_tools = [mcp_tool_to_openai(t) for t in mcp_tools]

    messages = cl.user_session.get("messages", [])
    messages.append({"role": "user", "content": message.content})

    max_iterations = 10

    for _ in range(max_iterations):
        response = await litellm.acompletion(
            model=LLM_MODEL,
            messages=messages,
            tools=openai_tools if openai_tools else None,
            **_THINKING_EXTRAS,
        )

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

    cl.user_session.set("messages", messages)


@cl.on_chat_end
async def on_chat_end():
    """Clean up the MCP connection on chat end."""
    done: asyncio.Event | None = cl.user_session.get("mcp_done")
    task: asyncio.Task | None = cl.user_session.get("mcp_task")
    if done:
        done.set()
    if task:
        with contextlib.suppress(Exception):
            await task
