# Adopt t-strings for SQL queries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a SQL template processor for PEP 750 t-strings and adopt it across the codebase to improve SQL safety and readability.

**Architecture:** A central `postgres_sql` utility in `folio_core` will process `Template` objects, converting them into standard `(query, params)` tuples compatible with `psycopg`.

**Tech Stack:** Python 3.14+, psycopg (v3).

---

### Task 1: Define SQL Template Processor

**Files:**
- Create: `packages/core/src/folio_core/sql.py`

- [ ] **Step 1: Create the SQL utility**

```python
from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class Interpolation(Protocol):
    value: Any
    expression: str
    format_spec: str | None
    conversion: str | None

@runtime_checkable
class Template(Protocol):
    strings: tuple[str, ...]
    interpolations: tuple[Interpolation, ...]

def postgres_sql(template: Any) -> tuple[str, tuple[Any, ...]]:
    """Processes a PEP 750 Template object for PostgreSQL.

    Returns a (query_string, parameters) tuple.
    """
    if not hasattr(template, "strings") or not hasattr(template, "interpolations"):
        raise ValueError("Object is not a PEP 750 Template")

    query_parts = []
    params = []

    for i, s in enumerate(template.strings):
        query_parts.append(s)
        if i < len(template.interpolations):
            query_parts.append("%s")
            params.append(template.interpolations[i].value)

    return "".join(query_parts), tuple(params)
```

- [ ] **Step 2: Add to `__init__.py`**

Modify: `packages/core/src/folio_core/__init__.py`
Add: `from .sql import postgres_sql`

### Task 2: Adopt t-strings in `indexer.py`

**Files:**
- Modify: `packages/doc-sync/src/folio_sync/indexer.py`

- [ ] **Step 1: Import `postgres_sql`**
- [ ] **Step 2: Convert queries to t-strings**

```python
# Example conversion
# Old:
# await cur.execute("SELECT content_hash FROM documents WHERE path = %s", (path,))
# New:
# await cur.execute(*postgres_sql(t"SELECT content_hash FROM documents WHERE path = {path}"))
```

### Task 3: Adopt t-strings in `get_document.py`

**Files:**
- Modify: `packages/mcp-server/src/folio_mcp/tools/get_document.py`

- [ ] **Step 1: Import `postgres_sql`**
- [ ] **Step 2: Convert queries to t-strings**

### Task 4: Verification

- [ ] **Step 1: Run tests**

Run: `uv run pytest packages/doc-sync/tests packages/mcp-server/tests`

- [ ] **Step 2: Commit changes**

```bash
git add .
git commit -m "feat: adopt t-strings for SQL queries (PEP 750)"
```
