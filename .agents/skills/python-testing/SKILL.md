---
name: python-testing
description: >
  Use esta skill sempre que escrever testes em Python neste projeto: ao adicionar funcionalidade
  nova, corrigir bug, revisar cobertura por camada FCIS (domain/infra/app), ou quando duvidar
  sobre o que mockar, como nomear testes, ou onde colocá-los. Aplique mesmo sem menção explícita
  — se há código novo ou modificado sem testes, esta skill se aplica. /
  Use this skill whenever writing tests in this Python project: adding new functionality, fixing
  bugs, reviewing per-layer FCIS coverage (domain/infra/app), or when unsure what to mock, how
  to name tests, or where to place them. Apply even without explicit mention — if there is new
  or modified code without tests, this skill applies.
---

# Python Testing — FCIS Layer Guide

Tests are not optional. Every new feature needs tests before it can be considered done. Every bug fix needs a regression test. Tests enable safe refactoring, document intended behavior, and catch regressions before they reach production.

## FCIS Testing Strategy

| Layer | Test type | Async | Mock policy | Coverage target |
|-------|-----------|-------|-------------|-----------------|
| `domain/` | Unit | No | Zero mocks | 95% |
| `infra/` | Unit | Yes | System boundary only | 80% |
| `app/` | Integration | Yes | External deps only | 70% |

**System boundary** = the outermost edge you do not own: filesystem driver, HTTP client class, DB connection. Never mock functions you wrote inside your own infra layer.

## File Structure

```
packages/<name>/
├── src/platform_<name>/
│   ├── domain/
│   ├── infra/
│   └── app/
└── tests/
    └── unit/
        ├── conftest.py          # shared fixtures for this package
        ├── test_<domain_mod>.py
        └── test_<infra_mod>.py

tests/                           # project root
├── integration/
│   ├── conftest.py              # shared fixtures (DB engine, server lifespan)
│   └── test_<feature>.py
└── fixtures/
    └── <data>.yaml
```

## Tools

Install test dependencies if missing:

```bash
uv add --dev pytest pytest-asyncio pytest-cov
```

Config in root `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests", "packages"]
addopts = "--cov=packages --cov-report=term-missing"

[tool.coverage.report]
fail_under = 80
```

## AAA Pattern

Every test has three sections: Arrange, Act, Assert. One behavior per test.

```python
def test_chunk_document_splits_on_max_tokens():
    # Arrange
    doc = make_document(content="word " * 200)
    config = ChunkConfig(max_tokens=50)

    # Act
    chunks = chunk_document(doc, config=config)

    # Assert
    assert all(len(c.content.split()) <= 50 for c in chunks)
```

Never put assertions in Arrange. Never combine two behaviors in one test — split them.

## Naming Convention

```
test_<unit>_<scenario>_<expected_outcome>

test_chunk_document_empty_content_returns_empty_list
test_embed_batch_api_timeout_returns_failure
test_run_ingestion_valid_directory_inserts_all_chunks
```

## conftest.py — When and Where

- Use `conftest.py` only when two or more tests in the same directory share a fixture
- Package-level `conftest.py` → domain model builders, config stubs
- Root `tests/conftest.py` → DB engine, server lifespan, shared async clients
- Inline fixtures (defined in the test file) for one-off setup

## Coverage

Run with coverage:

```bash
uv run pytest --cov=packages --cov-report=term-missing
```

Per-package:

```bash
uv run pytest packages/platform-ingestion/tests/ \
  --cov=packages/platform-ingestion/src \
  --cov-report=term-missing
```

Coverage targets are minimums, not goals. Prioritize testing behavior over chasing line numbers.

## Feature Checklist

- [ ] Unit tests for every new domain function (pure logic paths)
- [ ] Unit tests for infra adapter: happy path + at least one failure path
- [ ] Integration test if app-layer orchestration changed
- [ ] `uv run pytest` passes with no new failures
- [ ] Coverage does not drop below targets after changes

## Bugfix Checklist

- [ ] Write a failing test that reproduces the bug (before the fix)
- [ ] Fix the bug
- [ ] Confirm the test now passes
- [ ] Verify no related tests regressed

## Layer-Specific Reference

- `references/domain-testing.md` — Pure functions, parametrize, Result types, frozen dataclasses
- `references/infra-testing.md` — AsyncMock, tmp_path, boundary mocking, DB cleanup fixtures
- `references/app-testing.md` — Fixture composition, pipeline testing, lifespan context managers
