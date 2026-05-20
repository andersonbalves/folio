# /// script
# requires-python = ">=3.14"
# dependencies = ["anthropic>=0.52", "fastmcp>=3.3.1", "pyyaml>=6.0"]
# ///
"""MCP eval runner — tests folio-mcp trigger and response quality."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ExpectedTool:
    """A tool expected to be called in a scenario, with an optional required flag."""

    name: str
    required: bool = True


@dataclass
class Scenario:
    """A single eval scenario loaded from a YAML file."""

    id: str
    name: str
    question: str
    expected_tools: list[ExpectedTool]
    quality_criteria: list[str]


@dataclass
class ToolCall:
    """A recorded MCP tool call made during a scenario run."""

    tool: str
    args: dict
    result_len: int


@dataclass
class TriggerResult:
    """Outcome of checking whether expected tools were triggered."""

    required_called: bool
    unexpected_called: bool
    passed: bool
    missing: list[str]
    unexpected: list[str]


@dataclass
class ScenarioResult:
    """Full result of running a single eval scenario."""

    id: str
    name: str
    question: str
    tool_calls: list[ToolCall]
    final_answer: str
    trigger: TriggerResult


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def load_scenario(path: Path) -> Scenario:
    """Load and parse a scenario YAML file into a Scenario dataclass."""
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
    """Convert an MCP tool object to the Anthropic API tool dict format."""
    return {
        "name": mcp_tool.name,
        "description": mcp_tool.description or "",
        "input_schema": mcp_tool.inputSchema,
    }


def check_trigger_assertions(
    tool_calls: list[ToolCall],
    expected_tools: list[ExpectedTool],
) -> TriggerResult:
    """Check whether required tools were called and flag any unexpected ones."""
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


def main() -> None:
    """Entry point — agentic runner to be implemented in Task 3."""
    raise NotImplementedError("TODO: implement agentic runner (Task 3)")


if __name__ == "__main__":
    main()
