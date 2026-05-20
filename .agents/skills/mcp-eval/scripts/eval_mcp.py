# /// script
# requires-python = ">=3.14"
# dependencies = ["anthropic>=0.52", "fastmcp>=3.3.1", "pyyaml>=6.0"]
# ///
"""MCP eval runner — tests folio-mcp trigger and response quality."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path

import anthropic
import mcp.types
import yaml
from fastmcp import Client

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ExpectedTool:
    """A tool expected to be called in a scenario."""

    name: str
    required: bool = True


@dataclass
class Scenario:
    """A single eval scenario loaded from YAML."""

    id: str
    name: str
    question: str
    expected_tools: list[ExpectedTool]
    quality_criteria: list[str]


@dataclass
class ToolCall:
    """A recorded tool call from the agentic loop."""

    tool: str
    args: dict
    result_len: int


@dataclass
class TriggerResult:
    """Result of deterministic trigger assertions for a scenario."""

    required_called: bool
    unexpected_called: bool
    passed: bool
    missing: list[str]
    unexpected: list[str]


@dataclass
class ScenarioResult:
    """Full result for a single scenario run."""

    id: str
    name: str
    question: str
    tool_calls: list[ToolCall]
    final_answer: str
    trigger: TriggerResult


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested in test_eval_helpers.py)
# ---------------------------------------------------------------------------


def load_scenario(path: Path) -> Scenario:
    """Load a scenario from a YAML file."""
    data = yaml.safe_load(path.read_text())
    return Scenario(
        id=data["id"],
        name=data["name"],
        question=data["question"],
        expected_tools=[
            ExpectedTool(name=t["name"], required=t.get("required", True))
            for t in data.get("expected_tools", [])
        ],
        quality_criteria=data.get("quality_criteria", []),
    )


def mcp_tool_to_anthropic(mcp_tool) -> dict:
    """Convert a FastMCP Tool schema to Anthropic tool format."""
    return {
        "name": mcp_tool.name,
        "description": mcp_tool.description or "",
        "input_schema": mcp_tool.inputSchema,
    }


def check_trigger_assertions(
    tool_calls: list[ToolCall],
    expected_tools: list[ExpectedTool],
) -> TriggerResult:
    """Check deterministic trigger assertions for a scenario result."""
    called_names = {tc.tool for tc in tool_calls}
    expected_names = {et.name for et in expected_tools}
    required_names = {et.name for et in expected_tools if et.required}

    missing = [name for name in required_names if name not in called_names]
    unexpected = [name for name in called_names if name not in expected_names]

    return TriggerResult(
        required_called=len(missing) == 0,
        unexpected_called=len(unexpected) > 0,
        passed=len(missing) == 0,
        missing=missing,
        unexpected=unexpected,
    )


def _extract_mcp_result(result) -> str:
    parts = [block.text for block in result.content if isinstance(block, mcp.types.TextContent)]
    return "\n".join(parts) if parts else "(no result)"


# ---------------------------------------------------------------------------
# Agentic runner
# ---------------------------------------------------------------------------

MODEL = "claude-haiku-4-5-20251001"


async def run_scenario(
    client: anthropic.AsyncAnthropic,
    bridge: Client,
    scenario: Scenario,
    anthropic_tools: list[dict],
) -> ScenarioResult:
    """Run a single scenario: Haiku agentic loop against live folio-mcp."""
    messages: list[dict] = [{"role": "user", "content": scenario.question}]
    tool_calls: list[ToolCall] = []
    final_answer = ""

    while True:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=anthropic_tools,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    final_answer = block.text
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    try:
                        result = await bridge.call_tool(block.name, block.input or {})
                        result_text = _extract_mcp_result(result)
                    except Exception as exc:
                        result_text = f"[tool error: {exc}]"
                    tool_calls.append(
                        ToolCall(
                            tool=block.name,
                            args=block.input or {},
                            result_len=len(result_text),
                        )
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
        else:
            print(f"  Warning: unexpected stop_reason={response.stop_reason!r}")
            break

    trigger = check_trigger_assertions(tool_calls, scenario.expected_tools)
    return ScenarioResult(
        id=scenario.id,
        name=scenario.name,
        question=scenario.question,
        tool_calls=tool_calls,
        final_answer=final_answer,
        trigger=trigger,
    )


def format_report(results: list[ScenarioResult]) -> str:
    """Format eval results as a markdown report."""
    passed = sum(1 for r in results if r.trigger.passed)
    lines = [
        "# MCP Eval Report",
        f"\n**Trigger: {passed}/{len(results)} passed**\n",
    ]
    for r in results:
        status = "PASS" if r.trigger.passed else "FAIL"
        lines += [
            f"\n## [{status}] {r.id} — {r.name}",
            f"**Question:** {r.question}",
            f"**Tools called:** {[tc.tool for tc in r.tool_calls]}",
        ]
        if r.trigger.missing:
            lines.append(f"**Missing required:** {r.trigger.missing}")
        if r.trigger.unexpected:
            lines.append(f"**Unexpected (warning):** {r.trigger.unexpected}")
        lines.append(f"\n**Final answer (first 500 chars):**\n{r.final_answer[:500]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


async def main_async(args: argparse.Namespace) -> None:
    """Run all scenarios and print report."""
    scenarios_dir = Path(args.scenarios)
    scenario_files = sorted(scenarios_dir.glob("*.yaml"))

    if not scenario_files:
        print(f"No .yaml files found in {scenarios_dir}")
        return

    scenarios = [load_scenario(f) for f in scenario_files]
    print(f"Loaded {len(scenarios)} scenarios")

    mcp_parts = args.mcp_command.split()
    project_root = Path(__file__).parent.parent.parent.parent.parent
    mcp_config = {
        "mcpServers": {
            "folio": {
                "command": mcp_parts[0],
                "args": mcp_parts[1:],
                "cwd": str(project_root),
            }
        }
    }

    anthropic_client = anthropic.AsyncAnthropic()

    async with Client(mcp_config) as bridge:
        mcp_tools = await bridge.list_tools()
        anthropic_tools = [mcp_tool_to_anthropic(t) for t in mcp_tools]
        print(f"MCP tools: {[t.name for t in mcp_tools]}\n")

        results: list[ScenarioResult] = []
        for scenario in scenarios:
            print(f"Running {scenario.id}: {scenario.name}...")
            result = await run_scenario(anthropic_client, bridge, scenario, anthropic_tools)
            results.append(result)
            status = "PASS" if result.trigger.passed else "FAIL"
            print(f"  Trigger: {status}  tools={[tc.tool for tc in result.tool_calls]}")

    print("\n" + format_report(results))

    if args.output:
        output_data = [
            {
                "id": r.id,
                "name": r.name,
                "question": r.question,
                "tool_calls": [
                    {"tool": tc.tool, "args": tc.args, "result_len": tc.result_len}
                    for tc in r.tool_calls
                ],
                "final_answer": r.final_answer,
                "trigger": {
                    "required_called": r.trigger.required_called,
                    "unexpected_called": r.trigger.unexpected_called,
                    "passed": r.trigger.passed,
                    "missing": r.trigger.missing,
                    "unexpected": r.trigger.unexpected,
                },
            }
            for r in results
        ]
        Path(args.output).write_text(json.dumps(output_data, indent=2))
        print(f"\nResults saved to {args.output}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MCP eval runner — validates folio-mcp tool quality"
    )
    parser.add_argument(
        "--scenarios",
        default=".agents/skills/mcp-eval/scenarios/",
        help="Directory with YAML scenario files (default: .agents/skills/mcp-eval/scenarios/)",
    )
    parser.add_argument(
        "--mcp-command",
        default="uv run folio-mcp",
        help="Command to spawn folio-mcp server (default: uv run folio-mcp)",
    )
    parser.add_argument(
        "--output",
        help="Write JSON results to this path (optional)",
    )
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
