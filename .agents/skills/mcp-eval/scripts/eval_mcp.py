# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml>=6.0"]
# ///
"""MCP eval runner — tests folio-mcp trigger and response quality via claude -p CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

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


def _build_mcp_config(mcp_command: str, project_root: Path) -> dict:
    """Build MCP config dict for --mcp-config flag."""
    parts = mcp_command.split()
    return {
        "mcpServers": {
            "folio": {
                "command": parts[0],
                "args": parts[1:],
                "cwd": str(project_root),
            }
        }
    }


def _normalize_tool_name(name: str) -> str:
    """Strip mcp__<server>__ prefix added by Claude Code for MCP tools.

    Claude Code prefixes MCP tools as mcp__<servername>__<toolname>.
    Scenarios use short names (e.g. list_topics), so we strip the prefix
    to allow matching. Non-MCP tools (Read, Bash, etc.) pass through unchanged.
    """
    if name.startswith("mcp__"):
        parts = name.split("__", 2)
        if len(parts) == 3:
            return parts[2]
    return name


def parse_stream_json(output: str) -> tuple[list[ToolCall], str]:
    """Parse claude --output-format stream-json output into tool calls and final answer.

    Processes JSONL events:
    - "assistant" events: capture tool_use blocks (name + args)
    - "tool" events: capture result length for matching tool_use id
    - "result" event: capture final answer
    """
    tool_calls: list[ToolCall] = []
    tool_by_id: dict[str, ToolCall] = {}
    final_answer = ""

    for line in output.strip().splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type")

        if event_type == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tc = ToolCall(
                        tool=_normalize_tool_name(block["name"]),
                        args=block.get("input", {}),
                        result_len=0,
                    )
                    tool_calls.append(tc)
                    tool_by_id[block.get("id", "")] = tc

        elif event_type == "tool":
            tool_id = event.get("id", "")
            result_text = event.get("output", "") or ""
            if tool_id in tool_by_id:
                tool_by_id[tool_id].result_len = len(result_text)

        elif event_type == "result":
            final_answer = event.get("result", "")

    return tool_calls, final_answer


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

MODEL = "claude-haiku-4-5-20251001"


def run_scenario(scenario: Scenario, mcp_command: str, project_root: Path) -> ScenarioResult:
    """Run a single scenario via claude -p CLI against live folio-mcp."""
    config = _build_mcp_config(mcp_command, project_root)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        config_path = Path(f.name)

    try:
        proc = subprocess.run(
            [
                "claude",
                "-p",
                scenario.question,
                "--output-format",
                "stream-json",
                "--verbose",
                "--model",
                MODEL,
                "--mcp-config",
                str(config_path),
                "--strict-mcp-config",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            print(f"  Warning: claude exited with code {proc.returncode}")
            if proc.stderr:
                print(f"  stderr: {proc.stderr[:200]}")
        tool_calls, final_answer = parse_stream_json(proc.stdout)
    finally:
        config_path.unlink(missing_ok=True)

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

    scenarios_dir = Path(args.scenarios)
    scenario_files = sorted(scenarios_dir.glob("*.yaml"))

    if not scenario_files:
        print(f"No .yaml files found in {scenarios_dir}")
        return

    scenarios = [load_scenario(f) for f in scenario_files]
    project_root = Path(__file__).parent.parent.parent.parent.parent
    print(f"Loaded {len(scenarios)} scenarios")

    results: list[ScenarioResult] = []
    for scenario in scenarios:
        print(f"Running {scenario.id}: {scenario.name}...")
        result = run_scenario(scenario, args.mcp_command, project_root)
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


if __name__ == "__main__":
    main()
