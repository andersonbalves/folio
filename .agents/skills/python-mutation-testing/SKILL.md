---
name: python-mutation-testing
description: >
  Use esta skill ao executar mutation testing (mutmut) neste projeto: configurar mutmut por
  package, interpretar mutantes sobreviventes, escrever testes corretivos, ou integrar ao CI
  local. Aplique quando cobertura de linha já passa mas qualidade dos testes é incerta, ou ao
  revisar testes de camada domain/ especificamente. /
  Use this skill when running mutation testing (mutmut) in this project: configuring mutmut
  per package, interpreting surviving mutants, writing corrective tests, or integrating into
  local CI. Apply when line coverage already passes but test quality is uncertain, or when
  reviewing domain/ layer tests specifically.
---

# Python Mutation Testing — mutmut Guide

Line coverage measures which code runs during tests. It does not measure whether your assertions actually catch bugs. A test can reach every line without asserting anything meaningful.

Mutation testing creates "mutants" — broken versions of your code — by flipping operators, changing constants, and removing logic. If a test suite fails when the mutant runs, the mutant is **killed** (good). If all tests still pass with broken code, the mutant **survives** (bad: your assertions are not verifying the right behavior).

Run mutation testing after line coverage targets are met. It reveals where assertions are weak or absent.

## When to Run

- After reaching 80% overall / 95% domain line coverage
- Before merging significant changes to `domain/` layer
- When a bug escaped to production that tests should have caught
- As a periodic quality gate (weekly or per-sprint)

## Install

```bash
uv add --dev mutmut
```

## Configuration

Add to each package's `pyproject.toml`:

```toml
[tool.mutmut]
paths_to_mutate = "src/platform_<name>/domain/"
tests_to_run = "packages/<name>/tests/unit/"
runner = "uv run pytest -x -q"
```

Example for `platform-ingestion`:

```toml
[tool.mutmut]
paths_to_mutate = "src/platform_ingestion/domain/"
tests_to_run = "packages/platform-ingestion/tests/unit/"
runner = "uv run pytest -x -q"
```

Run from the workspace root:

```bash
uv run --package platform-ingestion mutmut run
```

## Score Targets

| Layer | Minimum score |
|-------|---------------|
| `domain/` | 85% |
| `infra/` | 70% |
| `app/` | not required |

`domain/` target is higher because pure functions have deterministic behavior that tests can fully verify. `infra/` is harder to score because some mutations (log message text, error strings) are not observable at the interface level.

## FCIS Mutation Priorities

**domain/ — run full mutation suite.** Every operator and constant matters. Pure functions have no I/O side effects to hide behind — all behavior is in the return value.

**infra/ — focus on boundary conditions.** Prioritize mutations in: `Success`/`Failure` construction, conditional checks on API responses, error handling branches. Skip mutations inside string formatting and log messages.

**app/ — skip or run selectively.** App functions mostly wire domain and infra together. Most meaningful mutations are caught by domain and infra tests. Run app mutations only when investigating wiring bugs.

## Run Commands

```bash
# Run all mutations (from workspace root)
uv run mutmut run

# Show summary
uv run mutmut results

# List surviving mutants
uv run mutmut results --show-suspicious

# Inspect a specific mutant
uv run mutmut show <id>

# Apply mutant to file (for manual investigation)
uv run mutmut apply <id>

# Revert applied mutant
uv run mutmut unapply <id>
```

## Triage Workflow

1. `uv run mutmut results` — note total survived count
2. `uv run mutmut results --show-suspicious` — list surviving mutant IDs
3. For each surviving mutant:
   - `uv run mutmut show <id>` — read the diff
   - Identify what behavior the mutant breaks
   - Write a test that would catch it, or strengthen an existing assertion
   - Confirm the mutant is now killed: re-run `uv run mutmut run`
4. Re-run full suite after fixes to update the score

See `references/surviving-mutants.md` for common patterns and corrective test templates.

## CI Integration

Add a `make mutation` target to `Makefile`:

```makefile
mutation:
	uv run --package platform-commons mutmut run
	uv run --package platform-ingestion mutmut run
	uv run --package platform-mcp mutmut run
	uv run mutmut results
```

To fail when score is below threshold, check the results output in a script:

```bash
#!/usr/bin/env bash
# scripts/check_mutation_score.sh
KILLED=$(uv run mutmut results | grep -oP '\d+(?= killed)')
TOTAL=$(uv run mutmut results | grep -oP '\d+(?= total)')
SCORE=$(echo "scale=2; $KILLED / $TOTAL * 100" | bc)

if (( $(echo "$SCORE < 85" | bc -l) )); then
    echo "Mutation score ${SCORE}% below 85% threshold"
    exit 1
fi
echo "Mutation score: ${SCORE}%"
```

Run `make mutation` locally before merging `domain/` changes. Do not add it to automated CI until baseline scores are established — mutation runs take minutes per package.
