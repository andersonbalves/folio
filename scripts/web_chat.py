"""Chainlit web chat interface using MCP and Localstack."""

import json
import os
from contextlib import AsyncExitStack

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

    stack = AsyncExitStack()
    cl.user_session.set("mcp_stack", stack)

    msg = cl.Message(content="Connecting to MCP Server...", author="System")
    await msg.send()

    try:
        sse = await stack.enter_async_context(sse_client(MCP_LAMBDA_URL))
        session = await stack.enter_async_context(ClientSession(sse[0], sse[1]))
        await session.initialize()
        cl.user_session.set("mcp_session", session)

        tools_response = await session.list_tools()
        tools = tools_response.tools
        cl.user_session.set("mcp_tools", tools)

        cl.user_session.set("messages", [{"role": "system", "content": SYSTEM_PROMPT}])

        msg.content = f"Connected! Found {len(tools)} tools: {', '.join([t.name for t in tools])}"
        await msg.update()
    except Exception as e:
        msg.content = f"Failed to connect to MCP: {str(e)}"
        await msg.update()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle user messages and execute LLM tool calls."""
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
        )

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

                        # Extract text
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

    cl.user_session.set("messages", messages)


@cl.on_chat_end
async def on_chat_end():
    """Clean up the MCP connection on chat end."""
    stack = cl.user_session.get("mcp_stack")
    if stack:
        await stack.aclose()
