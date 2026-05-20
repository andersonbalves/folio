# Test Coverage Improvement Design

**Date:** 2026-05-19
**Status:** Approved

## Goal

Raise unit test coverage with meaningful tests, enforce an 80% minimum per-commit via pre-commit hook, and reorganize the test directory layout to mirror the `src/` package namespace. Integration tests get their own subdirectory and a dedicated pytest marker.

---

## 1. Test Directory Restructure

### Layout

Each package's `tests/` directory is restructured to mirror `src/<package_name>/`:

```
packages/core/tests/
  folio_core/
    test_categorizer.py     ← moved
    test_hasher.py          ← moved
    test_parser.py          ← moved
    test_sql.py             ← new
  integration/              ← empty for now

packages/doc-sync/tests/
  folio_sync/
    test_indexer.py         ← moved
    test_sync_handler.py    ← moved (expanded)
  integration/
    test_e2e.py             ← moved from tests/

packages/mcp-server/tests/
  folio_mcp/
    test_chat_helpers.py    ← moved
    test_get_document.py    ← moved
    test_list_topics.py     ← moved
    test_mcp_handler.py     ← moved
    test_search_docs.py     ← moved
  conftest.py               ← stays at tests/ root (shared fixtures)
  integration/              ← empty for now
```

### Integration marker

`test_e2e.py` loses its `pytest.mark.skip` and gets `@pytest.mark.integration` instead. The marker is registered in `pytest.ini`:

```ini
markers =
    integration: marks tests that require live infrastructure (LocalStack + Postgres)
```

All test runs that should exclude integration tests use `-m "not integration"`.

---

## 2. Coverage Tooling

### Dependency

`pytest-cov` added to `[dependency-groups] dev` in root `pyproject.toml`.

### Configuration (root `pyproject.toml`)

```toml
[tool.coverage.run]
source = ["folio_core", "folio_sync", "folio_mcp"]
omit = [
    "*/config.py",
    "*/db.py",
    "*/__init__.py",
]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

**Omit rationale:** `config.py` (env var reads), `db.py` (connection pool setup), and `__init__.py` are thin I/O boundary wrappers with no meaningful logic to assert on. Excluding them keeps the 80% bar meaningful.

### Make targets

`make test` stays fast — no `--cov`:
```makefile
test:
    uv run pytest -m "not integration" -v
```

New `make coverage` target for developer exploration:
```makefile
coverage:
    uv run pytest -m "not integration" --cov --cov-report=term-missing
```

---

## 3. Pre-commit Hook

Added to the `local` repo section of `.pre-commit-config.yaml`:

```yaml
- id: unit-test-coverage
  name: unit tests + coverage gate (80%)
  entry: uv run pytest -m "not integration" --cov --cov-fail-under=80 -q --no-header
  language: system
  types: [python]
  pass_filenames: false
```

**Behavior:** Runs the full unit test suite with coverage whenever any `.py` file is staged. Fails the commit if coverage drops below 80%. Does not run on commits touching only non-Python files (docs, config, SQL).

---

## 4. New Tests

### `packages/core/tests/folio_core/test_sql.py` (new)

`folio_core/sql.py` contains `postgres_sql()`, a pure function that processes PEP 750 t-string templates into `(query, params)` tuples. It has zero tests today. Cases to cover:

- Happy path: one interpolation → `%s` placeholder + param extracted
- Multiple interpolations → multiple `%s` in order
- No interpolations → raw string, empty params
- Invalid input (no `.strings`/`.interpolations`) → raises `ValueError`

No mocks needed — pure function.

### `packages/doc-sync/tests/folio_sync/test_sync_handler.py` (expanded)

`folio_sync/handler.py` contains `_handle_event()`, an async function with real orchestration logic (markdown filtering, per-record error handling). Currently untested. Cases to cover:

- Records with `.md` keys → `get_text` + `upsert_document` called once each
- Records with non-`.md` keys → skipped
- `get_text` raises → error counted, processing continues for other records
- Empty event / no S3 records → returns `{"processed": 0, "errors": 0}`

Mock boundary: `folio_sync.handler.get_text`, `folio_sync.handler.upsert_document`, `folio_sync.handler.close_pool` — these are shell I/O functions being used by the handler, so mocking them is appropriate for unit-testing the handler's orchestration logic without hitting S3 or DB.

---

## 5. Implementation Sequence

1. **Restructure directories** — move existing test files, create `integration/` subdirs (no `__init__.py` needed; pytest discovers via rootdir)
2. **Update `test_e2e.py`** — replace `pytest.mark.skip` with `@pytest.mark.integration`
3. **Update `pytest.ini`** — register `integration` marker
4. **Add `pytest-cov`** — `uv add --dev pytest-cov`
5. **Add coverage config** — `[tool.coverage.run]` + `[tool.coverage.report]` in root `pyproject.toml`
6. **Update `Makefile`** — add `-m "not integration"` to `make test`, add `make coverage` target
7. **Write `test_sql.py`** — full coverage of `postgres_sql()`
8. **Expand `test_sync_handler.py`** — `_handle_event` orchestration tests
9. **Run `make coverage`** — verify 80% reached across all packages
10. **Add pre-commit hook** — append to `.pre-commit-config.yaml`, run `pre-commit install`
11. **Run `make check`** — confirm full pipeline passes

---

## Out of Scope

- Integration test expansion (only restructured, not written)
- Mutation testing (covered by separate skill)
- Per-package coverage thresholds (revisit if a package consistently drags the workspace-wide number)
