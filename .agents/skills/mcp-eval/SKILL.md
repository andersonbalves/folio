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

**Prerequisite:** folio infrastructure running. Verify with `docker-compose ps` — both `postgres` and `localstack` containers must show `Up`. Start with `make up` or `docker-compose up -d` if not running.

```bash
# Auto-detects CLI (claude preferred, falls back to agy)
uv run .agents/skills/mcp-eval/scripts/eval_mcp.py \
  --scenarios .agents/skills/mcp-eval/scenarios/ \
  --mcp-command "uv run folio-mcp" \
  --output /tmp/mcp-eval-results.json

# Force specific CLI
uv run .agents/skills/mcp-eval/scripts/eval_mcp.py \
  --cli agy \
  --scenarios .agents/skills/mcp-eval/scenarios/ \
  --mcp-command "uv run folio-mcp" \
  --output /tmp/mcp-eval-results.json
```

**CLI differences:**

| | `claude` | `agy` |
|---|---|---|
| Trigger detection | Full (stream-json) | Best-effort (log parsing) |
| MCP config | `--mcp-config` flag | Writes to `~/.gemini/config/mcp_config.json` (restored after) |
| Model | `claude-haiku-4-5-20251001` | IDE-configured model |

**agy trigger detection caveat:** tool calls are detected from `agy --log-file` entries. If `--dangerously-skip-permissions` bypasses the confirmation step in your version of `agy`, trigger detection will be unavailable and scenarios will show `[ANSWER-ONLY]` status. Evaluate final answer quality manually in that case.

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

**Required flag semantics:** `required: true` means the tool MUST be called or the trigger check fails. `required: false` means the tool is expected but its absence is a warning only—the trigger still passes. Use `true` for critical path tools, `false` for contextual helpers.
