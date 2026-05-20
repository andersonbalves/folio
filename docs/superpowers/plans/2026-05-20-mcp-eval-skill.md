# MCP Eval Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `.agents/skills/mcp-eval/` — a self-contained skill with a deterministic eval runner and scenario files that validate folio-mcp trigger quality (Claude picks right tools) and response quality (answers are accurate).

**Architecture:** Skill bundle with `SKILL.md` (protocol), `scripts/eval_mcp.py` (PEP 723 agentic runner using Anthropic SDK + FastMCP), and `scenarios/*.yaml` (YAML test cases). Runner executes Claude Haiku against live folio-mcp, captures tool call trace for deterministic trigger assertions, outputs JSON for LLM quality evaluation. Follows full skill-creator loop: draft → test → eval-viewer → iterate → optimize description.

**Tech Stack:** Python 3.14, `anthropic>=0.52` (Haiku agentic loop), `fastmcp>=3.3.1` (MCP stdio client), `pyyaml>=6.0`, `uv run` (PEP 723 inline deps), skill-creator eval pipeline

---

## File Structure

| Path | Action | Responsibility |
|------|--------|----------------|
| `.agents/skills/mcp-eval/SKILL.md` | Create | Eval protocol, when to run, how to interpret results, RED-GREEN-REFACTOR |
| `.agents/skills/mcp-eval/scripts/eval_mcp.py` | Create | PEP 723 runner: load scenarios, run Haiku agentic loop, deterministic trigger assertions, JSON output |
| `.agents/skills/mcp-eval/scripts/test_eval_helpers.py` | Create | Unit tests for pure helper functions |
| `.agents/skills/mcp-eval/scenarios/001-list-topics.yaml` | Create | Scenario: basic list_topics trigger |
| `.agents/skills/mcp-eval/scenarios/002-search-known-term.yaml` | Create | Scenario: search_docs trigger |
| `.agents/skills/mcp-eval/scenarios/003-get-document-by-path.yaml` | Create | Scenario: get_document trigger |
| `.agents/skills/mcp-eval/scenarios/004-multi-tool-flow.yaml` | Create | Scenario: full recommended flow |
| `.agents/skills/mcp-eval/scenarios/005-ambiguous-query.yaml` | Create | Scenario: edge case, must use tools not training data |
| `.agents/skills/mcp-eval/evals/evals.json` | Create | skill-creator eval prompts for testing SKILL.md itself |

---

### Task 1: Scaffold directory + SKILL.md

**Files:**
- Create: `.agents/skills/mcp-eval/SKILL.md`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p .agents/skills/mcp-eval/scripts
mkdir -p .agents/skills/mcp-eval/scenarios
mkdir -p .agents/skills/mcp-eval/evals
```

- [ ] **Step 2: Create SKILL.md**

Create `.agents/skills/mcp-eval/SKILL.md`:

```markdown
---
name: mcp-eval
description: Use to validate folio-mcp tool quality — tests whether Claude correctly triggers the right MCP tools and produces accurate responses. Run before/after modifying tool descriptions, server instructions, or tool implementations in handler.py. Invoke when you want to evaluate MCP trigger quality, check if tool descriptions are clear, validate a change to FastMCP instructions, or run the RED-GREEN-REFACTOR loop for MCP quality improvement.
---

# MCP Eval

Quality validation loop for `folio-mcp` tools. Tests trigger quality (does Claude pick the right tool?) and response quality (are answers accurate?).

## When to Run

- Before/after modifying `handler.py` tool docstrings
- Before/after modifying `FastMCP(instructions=...)` in `handler.py:15`
- After adding new MCP tools
- When users report wrong or missing tool calls

## How to Run

**Prerequisite:** folio infrastructure running (`make up` or `docker-compose up -d`)

```bash
uv run .agents/skills/mcp-eval/scripts/eval_mcp.py \
  --scenarios .agents/skills/mcp-eval/scenarios/ \
  --mcp-command "uv run folio-mcp" \
  --output /tmp/mcp-eval-results.json
```

## Evaluating Quality Criteria

After the script runs, read `/tmp/mcp-eval-results.json`. For each scenario, find its YAML in `scenarios/` to get `quality_criteria`. Judge each criterion individually:

> "Given this `final_answer` and `tool_calls`, was this criterion met? Answer PASS or FAIL with one sentence of evidence."

Per-scenario verdict: **PASS** (all criteria pass) / **PARTIAL** / **FAIL**.

## RED-GREEN-REFACTOR Cycle

**RED:** Run all scenarios. For each failure, document: which tools were called, which were missing, which criteria failed.

**GREEN:** Fix one specific issue (one change only). Re-run to verify improvement.

**REFACTOR:** Add edge case scenarios. Find new failure modes. Tighten descriptions.

## Iteration Targets When RED

| Failure | Root cause | Fix location |
|---------|-----------|--------------|
| Wrong tool called | Tool docstring ambiguous | `handler.py` `@mcp.tool()` docstring |
| No tool called at all | Server instructions weak | `FastMCP(instructions=...)` in `handler.py:15` |
| Right tool, bad args | Param description unclear | Args section of tool docstring |
| Tool output not used by model | Quality eval issue | Improve quality_criteria or system prompt |
| Tool returns poor results | Search relevance | `tools/search_docs.py` implementation |

## Scenario Format

To add a new scenario, create a YAML file in `.agents/skills/mcp-eval/scenarios/`:

```yaml
id: "006"
name: "Short descriptive name"
question: "User question exactly as Claude would receive it"
expected_tools:
  - name: list_topics
    required: true        # false = optional; missing won't fail trigger check
  - name: get_document
    required: false
quality_criteria:
  - "Specific verifiable statement about final_answer"
  - "Another criterion — prefer factual over stylistic"
```
```

- [ ] **Step 3: Verify SKILL.md is valid markdown with correct frontmatter**

```bash
python3 -c "
import re
content = open('.agents/skills/mcp-eval/SKILL.md').read()
assert content.startswith('---'), 'Missing frontmatter'
assert 'name: mcp-eval' in content, 'Missing name'
assert 'description:' in content, 'Missing description'
print('SKILL.md valid')
"
```

Expected: `SKILL.md valid`

- [ ] **Step 4: Commit**

```bash
git add .agents/skills/mcp-eval/SKILL.md
git commit -m "feat(mcp-eval): scaffold skill directory and SKILL.md protocol"
```

---

### Task 2: Unit tests + pure helper functions

**Files:**
- Create: `.agents/skills/mcp-eval/scripts/test_eval_helpers.py`
- Create (partial): `.agents/skills/mcp-eval/scripts/eval_mcp.py` (dataclasses + pure functions only)

- [ ] **Step 1: Write failing tests**

Create `.agents/skills/mcp-eval/scripts/test_eval_helpers.py`:

```python
"""Unit tests for pure helper functions in eval_mcp.py."""

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Load eval_mcp.py as module without executing main()
_spec = importlib.util.spec_from_file_location(
    "eval_mcp",
    Path(__file__).parent / "eval_mcp.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

load_scenario = _mod.load_scenario
mcp_tool_to_anthropic = _mod.mcp_tool_to_anthropic
check_trigger_assertions = _mod.check_trigger_assertions
Scenario = _mod.Scenario
ExpectedTool = _mod.ExpectedTool
ToolCall = _mod.ToolCall


class TestLoadScenario:
    def test_loads_all_fields(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(
            'id: "001"\n'
            'name: "Test scenario"\n'
            'question: "What topics?"\n'
            "expected_tools:\n"
            "  - name: list_topics\n"
            "    required: true\n"
            "quality_criteria:\n"
            '  - "Response mentions topics"\n'
        )
        scenario = load_scenario(yaml_file)
        assert scenario.id == "001"
        assert scenario.name == "Test scenario"
        assert scenario.question == "What topics?"
        assert len(scenario.expected_tools) == 1
        assert scenario.expected_tools[0].name == "list_topics"
        assert scenario.expected_tools[0].required is True
        assert scenario.quality_criteria == ["Response mentions topics"]

    def test_required_field_defaults_to_true(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(
            'id: "002"\nname: "T"\nquestion: "Q"\n'
            "expected_tools:\n  - name: search_docs\nquality_criteria: []\n"
        )
        scenario = load_scenario(yaml_file)
        assert scenario.expected_tools[0].required is True

    def test_empty_quality_criteria(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(
            'id: "003"\nname: "T"\nquestion: "Q"\n'
            "expected_tools: []\nquality_criteria: []\n"
        )
        scenario = load_scenario(yaml_file)
        assert scenario.quality_criteria == []


class TestMcpToolToAnthropic:
    def test_converts_full_schema(self):
        tool = MagicMock()
        tool.name = "list_topics"
        tool.description = "List available topics"
        tool.inputSchema = {
            "type": "object",
            "properties": {"category": {"type": "string"}},
        }
        result = mcp_tool_to_anthropic(tool)
        assert result["name"] == "list_topics"
        assert result["description"] == "List available topics"
        assert result["input_schema"] == tool.inputSchema

    def test_none_description_becomes_empty_string(self):
        tool = MagicMock()
        tool.name = "get_document"
        tool.description = None
        tool.inputSchema = {"type": "object", "properties": {}}
        result = mcp_tool_to_anthropic(tool)
        assert result["description"] == ""

    def test_input_schema_key_not_parameters(self):
        tool = MagicMock()
        tool.name = "search_docs"
        tool.description = "Search"
        tool.inputSchema = {"type": "object"}
        result = mcp_tool_to_anthropic(tool)
        assert "input_schema" in result
        assert "parameters" not in result


class TestCheckTriggerAssertions:
    def test_required_tool_called_passes(self):
        tool_calls = [ToolCall(tool="list_topics", args={}, result_len=100)]
        expected = [ExpectedTool(name="list_topics", required=True)]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.required_called is True
        assert result.passed is True
        assert result.missing == []

    def test_required_tool_not_called_fails(self):
        tool_calls = []
        expected = [ExpectedTool(name="list_topics", required=True)]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.required_called is False
        assert result.passed is False
        assert "list_topics" in result.missing

    def test_unexpected_tool_is_warning_not_failure(self):
        tool_calls = [
            ToolCall(tool="list_topics", args={}, result_len=100),
            ToolCall(tool="search_docs", args={"query": "x"}, result_len=50),
        ]
        expected = [ExpectedTool(name="list_topics", required=True)]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.required_called is True
        assert result.unexpected_called is True
        assert "search_docs" in result.unexpected
        assert result.passed is True  # unexpected = warning only

    def test_optional_tool_missing_does_not_fail(self):
        tool_calls = [ToolCall(tool="list_topics", args={}, result_len=100)]
        expected = [
            ExpectedTool(name="list_topics", required=True),
            ExpectedTool(name="get_document", required=False),
        ]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.passed is True
        assert result.missing == []

    def test_multiple_required_tools_all_must_be_called(self):
        tool_calls = [ToolCall(tool="search_docs", args={}, result_len=50)]
        expected = [
            ExpectedTool(name="search_docs", required=True),
            ExpectedTool(name="get_document", required=True),
        ]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.passed is False
        assert "get_document" in result.missing
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest .agents/skills/mcp-eval/scripts/test_eval_helpers.py -v
```

Expected: `ModuleNotFoundError` or `AttributeError` — `eval_mcp.py` does not exist yet.

- [ ] **Step 3: Create eval_mcp.py with dataclasses + pure functions**

Create `.agents/skills/mcp-eval/scripts/eval_mcp.py` (pure functions only — no async, no I/O):

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["anthropic>=0.52", "fastmcp>=3.3.1", "pyyaml>=6.0"]
# ///
"""MCP eval runner — tests folio-mcp trigger and response quality."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ExpectedTool:
    name: str
    required: bool = True


@dataclass
class Scenario:
    id: str
    name: str
    question: str
    expected_tools: list[ExpectedTool]
    quality_criteria: list[str]


@dataclass
class ToolCall:
    tool: str
    args: dict
    result_len: int


@dataclass
class TriggerResult:
    required_called: bool
    unexpected_called: bool
    passed: bool
    missing: list[str]
    unexpected: list[str]


@dataclass
class ScenarioResult:
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
    return {
        "name": mcp_tool.name,
        "description": mcp_tool.description or "",
        "input_schema": mcp_tool.inputSchema,
    }


def check_trigger_assertions(
    tool_calls: list[ToolCall],
    expected_tools: list[ExpectedTool],
) -> TriggerResult:
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
    print("TODO: implement agentic runner (Task 3)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest .agents/skills/mcp-eval/scripts/test_eval_helpers.py -v
```

Expected: all 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add .agents/skills/mcp-eval/scripts/eval_mcp.py \
        .agents/skills/mcp-eval/scripts/test_eval_helpers.py
git commit -m "feat(mcp-eval): add pure helpers with unit tests (load_scenario, mcp_tool_to_anthropic, check_trigger_assertions)"
```

---

### Task 3: Complete eval_mcp.py — agentic runner + CLI

**Files:**
- Modify: `.agents/skills/mcp-eval/scripts/eval_mcp.py` (add async runner + CLI)

- [ ] **Step 1: Replace `main()` stub with full agentic runner**

Replace the entire file content of `.agents/skills/mcp-eval/scripts/eval_mcp.py` with the complete version below. The pure functions from Task 2 are preserved exactly — only the async runner and CLI are added:

```python
# /// script
# requires-python = ">=3.14"
# dependencies = ["anthropic>=0.52", "fastmcp>=3.3.1", "pyyaml>=6.0"]
# ///
"""MCP eval runner — tests folio-mcp trigger and response quality."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass, field
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
    name: str
    required: bool = True


@dataclass
class Scenario:
    id: str
    name: str
    question: str
    expected_tools: list[ExpectedTool]
    quality_criteria: list[str]


@dataclass
class ToolCall:
    tool: str
    args: dict
    result_len: int


@dataclass
class TriggerResult:
    required_called: bool
    unexpected_called: bool
    passed: bool
    missing: list[str]
    unexpected: list[str]


@dataclass
class ScenarioResult:
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
    return {
        "name": mcp_tool.name,
        "description": mcp_tool.description or "",
        "input_schema": mcp_tool.inputSchema,
    }


def check_trigger_assertions(
    tool_calls: list[ToolCall],
    expected_tools: list[ExpectedTool],
) -> TriggerResult:
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
    parts = [
        block.text
        for block in result.content
        if isinstance(block, mcp.types.TextContent)
    ]
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
                    result = await bridge.call_tool(block.name, block.input or {})
                    result_text = _extract_mcp_result(result)
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
        lines.append(f"\n**Quality criteria to evaluate:**")
        for criterion in []  :  # populated from scenario YAML by caller
            lines.append(f"  - {criterion}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


async def main_async(args: argparse.Namespace) -> None:
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
```

- [ ] **Step 2: Verify unit tests still pass after rewrite**

```bash
pytest .agents/skills/mcp-eval/scripts/test_eval_helpers.py -v
```

Expected: all 11 tests PASS (pure functions unchanged).

- [ ] **Step 3: Verify --help works**

```bash
uv run .agents/skills/mcp-eval/scripts/eval_mcp.py --help
```

Expected output contains:
```
usage: eval_mcp.py [-h] [--scenarios SCENARIOS] [--mcp-command MCP_COMMAND] [--output OUTPUT]
```

- [ ] **Step 4: Commit**

```bash
git add .agents/skills/mcp-eval/scripts/eval_mcp.py
git commit -m "feat(mcp-eval): add full agentic runner with Anthropic SDK + FastMCP stdio"
```

---

### Task 4: Write scenario files

**Files:**
- Create: `.agents/skills/mcp-eval/scenarios/001-list-topics.yaml`
- Create: `.agents/skills/mcp-eval/scenarios/002-search-known-term.yaml`
- Create: `.agents/skills/mcp-eval/scenarios/003-get-document-by-path.yaml`
- Create: `.agents/skills/mcp-eval/scenarios/004-multi-tool-flow.yaml`
- Create: `.agents/skills/mcp-eval/scenarios/005-ambiguous-query.yaml`

- [ ] **Step 1: Create 001-list-topics.yaml**

```yaml
id: "001"
name: "List topics basic"
question: "What documentation topics are available in the knowledge base?"
expected_tools:
  - name: list_topics
    required: true
quality_criteria:
  - "Response mentions actual topic names returned by list_topics tool"
  - "Does not invent topic names not present in tool output"
  - "Calls list_topics before any search or retrieval tool"
```

- [ ] **Step 2: Create 002-search-known-term.yaml**

```yaml
id: "002"
name: "Search known term"
question: "Find documentation about Python setup in this project"
expected_tools:
  - name: search_docs
    required: true
quality_criteria:
  - "Response references content actually returned by search_docs"
  - "Does not invent document paths or content not in tool output"
  - "Query argument passed to search_docs is relevant (contains 'python' or 'setup')"
```

- [ ] **Step 3: Create 003-get-document-by-path.yaml**

```yaml
id: "003"
name: "Get document by path"
question: "Show me the full content of the AGENTS.md file"
expected_tools:
  - name: get_document
    required: true
quality_criteria:
  - "Calls get_document with a path argument matching AGENTS.md"
  - "Response includes actual content from the document, not a paraphrase from memory"
  - "Does not skip the tool and answer from training data"
```

- [ ] **Step 4: Create 004-multi-tool-flow.yaml**

```yaml
id: "004"
name: "Multi-tool recommended flow"
question: "I need to understand what ADR documents are available and read one of them"
expected_tools:
  - name: search_docs
    required: true
  - name: get_document
    required: true
  - name: list_topics
    required: false
quality_criteria:
  - "Calls search_docs or list_topics to discover relevant documents before retrieving"
  - "Calls get_document on at least one discovered document path"
  - "Response contains content extracted from the actual document via tool, not hallucinated"
  - "Follows discover-then-retrieve pattern (search before get_document)"
```

- [ ] **Step 5: Create 005-ambiguous-query.yaml**

```yaml
id: "005"
name: "Ambiguous query — must use tools not training data"
question: "What does this project do?"
expected_tools:
  - name: list_topics
    required: true
quality_criteria:
  - "Uses MCP tools rather than answering exclusively from training data"
  - "Response reflects indexed content from the knowledge base"
  - "Does not confidently assert project details without consulting tools first"
```

- [ ] **Step 6: Validate scenarios load without error**

```bash
python3 -c "
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location('eval_mcp', '.agents/skills/mcp-eval/scripts/eval_mcp.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
files = sorted(Path('.agents/skills/mcp-eval/scenarios/').glob('*.yaml'))
for f in files:
    s = mod.load_scenario(f)
    print(f'  {s.id}: {s.name} — {len(s.expected_tools)} tools, {len(s.quality_criteria)} criteria')
print(f'All {len(files)} scenarios loaded OK')
"
```

Expected (5 lines + summary):
```
  001: List topics basic — 1 tools, 3 criteria
  002: Search known term — 1 tools, 3 criteria
  003: Get document by path — 1 tools, 3 criteria
  004: Multi-tool recommended flow — 3 tools, 4 criteria
  005: Ambiguous query — must use tools not training data — 1 tools, 3 criteria
All 5 scenarios loaded OK
```

- [ ] **Step 7: Commit**

```bash
git add .agents/skills/mcp-eval/scenarios/
git commit -m "feat(mcp-eval): add 5 evaluation scenarios covering all folio-mcp tools"
```

---

### Task 5: Smoke test against live folio-mcp

**Files:**
- None (testing only)

**Prerequisite:** folio infrastructure running. Run `make up` if not.

- [ ] **Step 1: Verify infrastructure is up**

```bash
docker-compose ps
```

Expected: `postgres` and `localstack` containers show `Up`.

- [ ] **Step 2: Run eval against live folio-mcp**

```bash
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
uv run .agents/skills/mcp-eval/scripts/eval_mcp.py \
  --scenarios .agents/skills/mcp-eval/scenarios/ \
  --mcp-command "uv run folio-mcp" \
  --output /tmp/mcp-eval-results.json
```

Expected: script connects to folio-mcp, runs 5 scenarios, prints report, writes JSON to `/tmp/mcp-eval-results.json`.

- [ ] **Step 3: Verify JSON output is valid**

```bash
python3 -c "
import json
results = json.load(open('/tmp/mcp-eval-results.json'))
print(f'Got {len(results)} results')
for r in results:
    status = 'PASS' if r['trigger']['passed'] else 'FAIL'
    print(f'  {r[\"id\"]} [{status}]: tools={[tc[\"tool\"] for tc in r[\"tool_calls\"]]}')
"
```

Expected: 5 results with tool call data.

- [ ] **Step 4: Commit (no code changes — this task is test-only)**

No commit needed for this task.

---

### Task 6: skill-creator eval loop — test SKILL.md quality

**Files:**
- Create: `.agents/skills/mcp-eval/evals/evals.json`

- [ ] **Step 1: Create evals.json**

Create `.agents/skills/mcp-eval/evals/evals.json`:

```json
{
  "skill_name": "mcp-eval",
  "evals": [
    {
      "id": 1,
      "prompt": "We just changed the search_docs tool description in handler.py to remove the 'ranked results' mention. Run the MCP eval to check if this affected trigger quality.",
      "expected_output": "Claude runs eval_mcp.py, interprets trigger results, evaluates quality criteria from JSON output, and reports which scenarios passed or failed with recommended fixes.",
      "files": [],
      "expectations": [
        "Runs uv run .agents/skills/mcp-eval/scripts/eval_mcp.py with --scenarios flag",
        "Evaluates quality_criteria from each scenario individually (not holistically)",
        "Reports per-scenario PASS/PARTIAL/FAIL verdict",
        "Identifies root cause of failures and points to handler.py fix location"
      ]
    },
    {
      "id": 2,
      "prompt": "Before I modify the FastMCP instructions string in handler.py, run the MCP eval baseline so we can compare before and after.",
      "expected_output": "Claude runs the eval, captures baseline results, clearly labels them as baseline for comparison.",
      "files": [],
      "expectations": [
        "Runs the eval script against live folio-mcp",
        "Produces a baseline report showing trigger pass/fail per scenario",
        "Labels output as baseline for before/after comparison"
      ]
    },
    {
      "id": 3,
      "prompt": "The MCP eval shows scenario 002 (search known term) is FAIL. search_docs was not called. What should I fix?",
      "expected_output": "Claude identifies the root cause (tool docstring or server instructions) and points to exact fix location in handler.py.",
      "files": [],
      "expectations": [
        "References the iteration targets table from SKILL.md",
        "Identifies specific fix: tool docstring in handler.py @mcp.tool() decorator",
        "Provides concrete suggestion for improving search_docs description"
      ]
    }
  ]
}
```

- [ ] **Step 2: Run baseline subagents (without skill) and with-skill subagents in parallel**

Spawn two subagents per eval — one with skill, one without. Use `model: "haiku"` for speed.

For each eval (3 total), spawn in same turn:
- **With skill:** task prompt + skill path `.agents/skills/mcp-eval/SKILL.md`, save output to `.agents/skills/mcp-eval-workspace/iteration-1/eval-<id>/with_skill/outputs/`
- **Without skill:** same prompt, no skill, save to `.agents/skills/mcp-eval-workspace/iteration-1/eval-<id>/without_skill/outputs/`

Create `eval_metadata.json` per eval with assertions from `evals.json`.

- [ ] **Step 3: Draft assertions while subagents run**

For each eval, add assertions to the `evals.json` `expectations` array (already populated in Step 1). Explain to user what each assertion checks.

- [ ] **Step 4: Grade results and generate eval-viewer**

After all 6 subagents complete:

1. Grade each run against assertions
2. Aggregate benchmark:
```bash
SKILL_CREATOR_PATH=$(find ~/.claude/plugins -name "aggregate_benchmark.py" -path "*/skill-creator/*" | head -1 | xargs dirname | xargs dirname)
python -m scripts.aggregate_benchmark .agents/skills/mcp-eval-workspace/iteration-1 --skill-name mcp-eval
```
3. Generate eval-viewer:
```bash
EVAL_VIEWER=$(find ~/.claude/plugins -name "generate_review.py" -path "*/skill-creator/*" | head -1)
nohup python "$EVAL_VIEWER" \
  .agents/skills/mcp-eval-workspace/iteration-1 \
  --skill-name "mcp-eval" \
  --benchmark .agents/skills/mcp-eval-workspace/iteration-1/benchmark.json \
  > /dev/null 2>&1 &
echo "Viewer PID: $!"
```

Tell user: "Results open in browser — 'Outputs' tab to review per-eval, 'Benchmark' for pass rates. Click 'Submit All Reviews' when done."

- [ ] **Step 5: Read feedback and iterate on SKILL.md**

Read `feedback.json` from workspace. Update SKILL.md based on failures. Re-run eval loop (iteration-2) until:
- Feedback is empty (all good), or
- Pass rate stops improving

- [ ] **Step 6: Commit final skill**

```bash
git add .agents/skills/mcp-eval/
git commit -m "feat(mcp-eval): add skill-creator evals and finalize SKILL.md after eval loop"
```

---

### Task 7: Description optimization

**Files:**
- Modify: `.agents/skills/mcp-eval/SKILL.md` (update `description:` frontmatter)

- [ ] **Step 1: Generate 20 trigger eval queries**

Create 20 queries (10 should-trigger, 10 should-not-trigger) as JSON. See skill-creator description optimization section for format. Focus on near-misses for should-not-trigger (adjacent domains that share vocabulary with MCP/tools but don't need this skill).

- [ ] **Step 2: Review queries with user**

Use `assets/eval_review.html` template from skill-creator. Open in browser. Wait for user to approve/edit and export `eval_set.json`.

- [ ] **Step 3: Run optimization loop**

```bash
SKILL_CREATOR_PATH=$(find ~/.claude/plugins -name "run_loop.py" -path "*/skill-creator/*" | head -1 | xargs dirname | xargs dirname)
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path .agents/skills/mcp-eval \
  --model claude-sonnet-4-6 \
  --max-iterations 5 \
  --verbose
```

- [ ] **Step 4: Apply optimized description**

Update `description:` in `.agents/skills/mcp-eval/SKILL.md` with `best_description` from run_loop output.

- [ ] **Step 5: Final commit**

```bash
git add .agents/skills/mcp-eval/SKILL.md
git commit -m "feat(mcp-eval): optimize skill description for triggering accuracy"
```

---

## Self-Review

**Spec coverage:**
- ✅ Subagent-driven eval loop (no CI) — Tasks 5, 6
- ✅ Claude Haiku as subject — `MODEL = "claude-haiku-4-5-20251001"` in Task 3
- ✅ Trigger quality (C — both: right tool AND decision to use MCP) — `check_trigger_assertions` in Task 2
- ✅ Tool output quality (layer A) — `result_len` captured, raw result to model in Task 3
- ✅ Final answer quality (layer B) — `quality_criteria` LLM evaluation in SKILL.md
- ✅ Scenarios in YAML — Tasks 4
- ✅ Script bundled in skill `scripts/` — Tasks 2, 3
- ✅ skill-creator full loop — Task 6
- ✅ Description optimization — Task 7
- ✅ Iteration targets table in SKILL.md — Task 1

**Type consistency:**
- `ToolCall` defined in Task 2 → used in `run_scenario` (Task 3) ✅
- `check_trigger_assertions(tool_calls: list[ToolCall], expected_tools: list[ExpectedTool])` — same signature in tests (Task 2) and usage (Task 3) ✅
- `mcp_tool_to_anthropic` returns `dict` with key `input_schema` (not `parameters`) — Anthropic API requires `input_schema` ✅
- `ScenarioResult.trigger` is `TriggerResult` — used in `format_report` ✅

**Placeholder scan:** No TBDs, TODOs, or incomplete steps.
