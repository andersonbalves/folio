# Design: MCP Eval Skill

**Date:** 2026-05-20
**Status:** Approved

## Overview

A subagent-driven quality validation loop for the `folio-mcp` server, testing both trigger quality (does Claude pick the right tool?) and response quality (are tool outputs and final answers correct?). Modeled on the skills testing RED-GREEN-REFACTOR cycle.

## Goals

- Validate that Claude Haiku correctly invokes MCP tools given realistic user questions
- Detect regressions when tool descriptions or server instructions change
- Produce actionable fix recommendations pointing to specific lines in `handler.py`
- Follow skill-creator full loop: draft → test → eval-viewer → iterate → optimize description

## Non-Goals

- CI integration or automated regression guard (subagent-driven only)
- Testing Ollama model behavior (Claude Haiku only)
- Testing MCP tool implementations at the unit level (existing pytest coverage handles that)

## Architecture

```
.agents/skills/mcp-eval/
  SKILL.md                         ← eval protocol (when/how/what to fix)
  scripts/
    eval_mcp.py                    ← PEP 723 deterministic runner
  scenarios/
    001-list-topics.yaml
    002-search-known-term.yaml
    003-get-document-by-path.yaml
    004-multi-tool-flow.yaml
    005-ambiguous-query.yaml       ← edge case
```

Two artifacts: skill defines protocol, script does work. Self-contained — scenarios and runner bundled with skill.

## Eval Flow

```
1. Claude invokes mcp-eval skill
2. SKILL.md instructs: run scripts/eval_mcp.py --scenarios scenarios/
3. Script per scenario:
   a. Connects to folio-mcp via FastMCP stdio Client
   b. Converts MCP tool schemas → Anthropic tools format
   c. Runs agentic loop with claude-haiku-4-5 (tool_use → tool_result → …)
   d. Captures full tool call trace (name + args + result_preview)
   e. Runs deterministic trigger assertions
   f. Outputs JSON: {tool_calls, final_answer, trigger_result}
4. Main Claude reads JSON output
5. Per quality_criteria item: LLM-judges pass/fail individually
6. Report: RED/GREEN per scenario + root cause + recommended fix
7. User iterates on handler.py docstrings or FastMCP(instructions=...)
8. Re-run until GREEN
```

### Agentic Loop (in script)

```
Initial call → Haiku with tools
  has tool_use?
    YES → call_tool(name, args) via FastMCP
          append tool_result
          record to trace
          → next call
    NO  → end_turn → final_answer
```

## Components

### `eval_mcp.py` (PEP 723)

```
Dependencies: anthropic, fastmcp, pyyaml

Per scenario:
  1. FastMCP Client → list_tools() → MCP schemas
  2. mcp_tool_to_anthropic(schema) → Anthropic tools format
  3. Anthropic SDK → claude-haiku-4-5 with tools
  4. Agentic loop: accumulate trace [{tool, args, result_len}]
  5. Deterministic trigger assertions
  6. Emit JSON result

CLI: uv run .agents/skills/mcp-eval/scripts/eval_mcp.py \
       --scenarios .agents/skills/mcp-eval/scenarios/ \
       --mcp-command "uv run folio-mcp"
```

Output JSON per scenario:
```json
{
  "id": "001",
  "name": "List topics basic",
  "question": "What documentation topics are available?",
  "tool_calls": [
    {"tool": "list_topics", "args": {}, "result_len": 450}
  ],
  "final_answer": "The available topics are...",
  "trigger": {
    "required_called": true,
    "unexpected_called": false,
    "passed": true
  }
}
```

### Scenario YAML Format

```yaml
id: "001"
name: "List topics basic"
question: "What documentation topics are available?"
expected_tools:
  - name: list_topics
    required: true
quality_criteria:
  - "Response mentions actual topic names returned by list_topics"
  - "Does not invent topics not present in tool output"
  - "Calls list_topics before any other tool"
```

### Deterministic Trigger Assertions (script)

For each scenario, script checks:
- `required_called`: all `required: true` tools in `expected_tools` were called
- `unexpected_called`: any tool NOT in `expected_tools` was called (warning only)

Pass/fail is binary and deterministic — no LLM involved.

### Quality Evaluation (main Claude)

After script runs, main Claude evaluates `quality_criteria` per scenario:
- For each criterion: "Given final_answer and tool_calls, was this criterion met? Answer PASS or FAIL with one sentence of evidence."
- Binary per criterion
- Scenario verdict: PASS (all criteria) / PARTIAL / FAIL

## Initial Scenario Set

| ID | Name | Expected Tools | Tests |
|----|------|----------------|-------|
| 001 | List topics basic | `list_topics` | Correct tool, no hallucination |
| 002 | Search known term | `search_docs` | Correct args, relevant results used |
| 003 | Get document by path | `list_topics → get_document` | Multi-step flow, correct path |
| 004 | Multi-tool flow | `list_topics → search_docs → get_document` | Full recommended flow |
| 005 | Ambiguous query | `search_docs` | Doesn't hallucinate when results sparse |

## Iteration Targets When RED

| Failure type | Root cause | Fix location |
|---|---|---|
| Wrong tool called | Tool docstring ambiguous | `handler.py` `@mcp.tool()` docstring |
| No tool called | Server instructions weak | `FastMCP(instructions=...)` in `handler.py:15` |
| Right tool, bad args | Param description unclear | Args section of tool docstring |
| Tool output not used | Model ignores result | Quality eval → model capability issue |
| Tool result poor quality | Search relevance low | Tool implementation in `tools/search_docs.py` |

## RED-GREEN-REFACTOR Cycle

**RED:** Run all scenarios. Document exact failures — which tools called, which missed, which criteria failed.

**GREEN:** Fix specific identified issue (one change at a time). Re-run to verify improvement.

**REFACTOR:** Add edge case scenarios. Find new failure modes. Tighten descriptions without over-constraining.

## Skill Creation Process

Follow skill-creator full loop:
1. Draft SKILL.md + eval_mcp.py + initial scenarios
2. Run 2-3 test prompts against skill with subagents
3. Generate eval-viewer for human review
4. Iterate based on feedback
5. Run description optimization (`run_loop.py`) once skill is stable

## File Locations

| Path | Action |
|------|--------|
| `.agents/skills/mcp-eval/SKILL.md` | Create |
| `.agents/skills/mcp-eval/scripts/eval_mcp.py` | Create |
| `.agents/skills/mcp-eval/scenarios/001-list-topics.yaml` | Create |
| `.agents/skills/mcp-eval/scenarios/002-search-known-term.yaml` | Create |
| `.agents/skills/mcp-eval/scenarios/003-get-document-by-path.yaml` | Create |
| `.agents/skills/mcp-eval/scenarios/004-multi-tool-flow.yaml` | Create |
| `.agents/skills/mcp-eval/scenarios/005-ambiguous-query.yaml` | Create |

No changes to existing packages or pyproject.toml.
