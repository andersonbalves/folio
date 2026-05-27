# Repo Reorganization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize folio into 4 packages (folio-core, folio-sync, folio-mcp, folio-chat) each with explicit `core/` and `shell/` sub-packages, remove all Lambda artifacts, move infrastructure to `infra/`, and expose folio-sync and folio-mcp as docker-compose services.

**Architecture:** folio-core shrinks to only what is genuinely shared across packages (`models.py`, `sql.py`). Each other package owns its pure functions in `package/core/` and its I/O layer in `package/shell/`. folio-chat is a new package for the Chainlit UI and CLI REPL, moving out of `scripts/`.

**Tech Stack:** Python 3.14, uv workspace monorepo, FastMCP, psycopg3, dynaconf, Chainlit, docker-compose

---

## File Map

### Created
```
packages/doc-sync/src/folio_sync/core/__init__.py
packages/doc-sync/src/folio_sync/core/parser.py         ← moved from folio-core
packages/doc-sync/src/folio_sync/core/hasher.py          ← moved from folio-core
packages/doc-sync/src/folio_sync/core/categorizer.py     ← moved from folio-core
packages/doc-sync/src/folio_sync/core/indexer.py         ← new: pure prepare_document()
packages/doc-sync/src/folio_sync/shell/__init__.py
packages/doc-sync/src/folio_sync/shell/config.py         ← moved from folio_sync/config.py
packages/doc-sync/src/folio_sync/shell/db.py             ← moved from folio_sync/db.py
packages/doc-sync/src/folio_sync/shell/s3_client.py      ← moved from folio_sync/s3_client.py
packages/doc-sync/src/folio_sync/shell/indexer.py        ← I/O part, calls core/indexer.py
packages/doc-sync/src/folio_sync/shell/handler.py        ← moved from folio_sync/handler.py, no lambda
packages/doc-sync/tests/folio_sync/core/__init__.py
packages/doc-sync/tests/folio_sync/core/test_parser.py   ← moved from folio-core tests
packages/doc-sync/tests/folio_sync/core/test_hasher.py   ← moved from folio-core tests
packages/doc-sync/tests/folio_sync/core/test_categorizer.py ← moved from folio-core tests
packages/doc-sync/tests/folio_sync/core/test_indexer.py  ← new: tests for prepare_document()
packages/doc-sync/tests/folio_sync/shell/__init__.py
packages/doc-sync/tests/folio_sync/shell/test_indexer.py ← updated from tests/folio_sync/test_indexer.py
packages/mcp-server/src/folio_mcp/core/__init__.py
packages/mcp-server/src/folio_mcp/core/queries.py        ← new: pure SQL builders
packages/mcp-server/src/folio_mcp/core/mappers.py        ← new: row → Pydantic mappers
packages/mcp-server/src/folio_mcp/shell/__init__.py
packages/mcp-server/src/folio_mcp/shell/config.py        ← moved from folio_mcp/config.py
packages/mcp-server/src/folio_mcp/shell/db.py            ← moved from folio_mcp/db.py
packages/mcp-server/src/folio_mcp/shell/tools/__init__.py
packages/mcp-server/src/folio_mcp/shell/tools/search_docs.py   ← moved + uses core
packages/mcp-server/src/folio_mcp/shell/tools/list_topics.py   ← moved + uses core
packages/mcp-server/src/folio_mcp/shell/tools/get_document.py  ← moved + uses core
packages/mcp-server/src/folio_mcp/shell/handler.py       ← moved, no lambda
packages/mcp-server/tests/folio_mcp/core/__init__.py
packages/mcp-server/tests/folio_mcp/core/test_queries.py ← new
packages/mcp-server/tests/folio_mcp/core/test_mappers.py ← new
packages/mcp-server/tests/folio_mcp/shell/__init__.py
packages/mcp-server/tests/folio_mcp/shell/test_search_docs.py  ← moved + updated
packages/mcp-server/tests/folio_mcp/shell/test_list_topics.py  ← moved + updated
packages/mcp-server/tests/folio_mcp/shell/test_get_document.py ← moved + updated
packages/mcp-server/tests/folio_mcp/shell/test_mcp_handler.py  ← moved + updated
packages/chat/
packages/chat/pyproject.toml
packages/chat/src/folio_chat/__init__.py
packages/chat/src/folio_chat/core/__init__.py
packages/chat/src/folio_chat/shell/__init__.py
packages/chat/src/folio_chat/shell/app.py                ← moved from scripts/web_chat.py
packages/chat/src/folio_chat/shell/chat.py               ← moved from scripts/chat.py
packages/mcp-server/tests/folio_chat/test_chat_helpers.py ← updated import path
packages/doc-sync/Dockerfile
packages/mcp-server/Dockerfile
infra/
infra/docker/localstack-init/01-bootstrap-aws.sh         ← moved from docker/
infra/migrations/                                         ← moved from migrations/
infra/seed/                                               ← moved from seed/
infra/scripts/apply_migrations.py                        ← moved from scripts/
infra/scripts/seed_localstack.py                         ← moved from scripts/
infra/scripts/run_full_sync.py                           ← moved from scripts/
```

### Modified
```
packages/core/src/folio_core/__init__.py       remove parser/hasher/categorizer exports
packages/core/pyproject.toml                   drop pyyaml (only used by parser)
packages/doc-sync/pyproject.toml               update scripts entry point
packages/mcp-server/pyproject.toml             update scripts entry point
packages/doc-sync/tests/integration/test_e2e.py  update imports
pyproject.toml                                 add folio-chat workspace member + dep
docker-compose.yml                             add folio-sync + folio-mcp services
Makefile                                       remove Lambda targets, update all paths
AGENTS.md                                      new package table, FCIS section
.agents/skills/python-fcis/SKILL.md            reflect core/shell subdir pattern
chainlit.md                                    move to packages/chat/chainlit.md
```

### Deleted
```
packages/core/src/folio_core/parser.py
packages/core/src/folio_core/hasher.py
packages/core/src/folio_core/categorizer.py
packages/core/tests/folio_core/test_parser.py
packages/core/tests/folio_core/test_hasher.py
packages/core/tests/folio_core/test_categorizer.py
packages/doc-sync/src/folio_sync/config.py
packages/doc-sync/src/folio_sync/db.py
packages/doc-sync/src/folio_sync/s3_client.py
packages/doc-sync/src/folio_sync/indexer.py
packages/doc-sync/src/folio_sync/handler.py
packages/doc-sync/tests/folio_sync/test_indexer.py
packages/doc-sync/tests/folio_sync/test_sync_handler.py
packages/mcp-server/src/folio_mcp/config.py
packages/mcp-server/src/folio_mcp/db.py
packages/mcp-server/src/folio_mcp/tools/             (whole directory)
packages/mcp-server/src/folio_mcp/handler.py
packages/mcp-server/tests/folio_mcp/test_search_docs.py
packages/mcp-server/tests/folio_mcp/test_list_topics.py
packages/mcp-server/tests/folio_mcp/test_get_document.py
packages/mcp-server/tests/folio_mcp/test_mcp_handler.py
packages/mcp-server/tests/folio_mcp/test_chat_helpers.py
Dockerfile.lambda
scripts/build_lambdas.sh
scripts/deploy_lambdas.sh
scripts/deploy_mcp_lwa.sh
scripts/run_chainlit.py
scripts/web_chat.py
scripts/chat.py
scripts/apply_migrations.py
scripts/seed_localstack.py
scripts/run_full_sync.py
docker/
migrations/
seed/
```

---

## Task 1: Write design spec

**Files:**
- Create: `docs/superpowers/specs/2026-05-26-repo-reorganization-design.md`

- [ ] **Step 1: Verify spec is missing**

```bash
ls docs/superpowers/specs/ | grep reorganization
```
Expected: no output (file missing from previous session commit failure).

- [ ] **Step 2: Write spec file**

```bash
cat > docs/superpowers/specs/2026-05-26-repo-reorganization-design.md << 'SPEC'
# Repo Reorganization Design

**Date:** 2026-05-26
**Status:** Approved

## Context

Three problems drove this redesign:

1. **Lambda/LocalStack incompatibility** — MCP server used Lambda Web Adapter with container
   images, which requires LocalStack Pro. Community edition does not support container image Lambdas.
2. **FCIS boundary violation** — `folio-core` contained `parser.py`, `hasher.py`,
   `categorizer.py` used exclusively by `folio-sync`. Shared core should only hold what is
   genuinely shared.
3. **Loose structure** — `scripts/` mixed deployment, seed, chat, and migration concerns;
   Docker assets scattered at root; no clear home for the Chainlit UI.

---

## Package Structure

Four packages, each with explicit `core/` and `shell/` sub-packages:

```
packages/
├── core/               folio-core  (shared minimum)
│   └── src/folio_core/
│       ├── models.py   (domain types used by ≥2 packages)
│       └── sql.py      (postgres_sql t-string helper)
│
├── doc-sync/           folio-sync  (S3 → Postgres sync)
│   └── src/folio_sync/
│       ├── core/
│       │   ├── parser.py       (← moved from folio-core)
│       │   ├── hasher.py       (← moved from folio-core)
│       │   ├── categorizer.py  (← moved from folio-core)
│       │   └── indexer.py      (pure: raw str → Document fields, no I/O)
│       └── shell/
│           ├── db.py
│           ├── s3_client.py
│           ├── indexer.py      (I/O: calls core indexer + writes to DB)
│           ├── config.py
│           └── handler.py
│
├── mcp-server/         folio-mcp
│   └── src/folio_mcp/
│       ├── core/
│       │   ├── queries.py      (pure SQL builders: returns (str, tuple))
│       │   └── mappers.py      (pure: DB rows → Pydantic models)
│       └── shell/
│           ├── db.py
│           ├── config.py
│           ├── tools/
│           │   ├── search_docs.py
│           │   ├── list_topics.py
│           │   └── get_document.py
│           └── handler.py
│
└── chat/               folio-chat  (new)
    └── src/folio_chat/
        ├── core/
        └── shell/
            ├── app.py          (Chainlit web UI ← from scripts/)
            └── chat.py         (CLI REPL ← from scripts/)
```

## Import Rules

| From → To | Allowed |
|-----------|---------|
| `folio_sync.core.*` → `folio_core` | ✓ |
| `folio_sync.shell.*` → `folio_sync.core.*` | ✓ |
| `folio_sync.shell.*` → `folio_core` | ✓ |
| `folio_mcp.core.*` → `folio_core` | ✓ |
| `folio_mcp.shell.*` → `folio_mcp.core.*` | ✓ |
| `folio_mcp.shell.*` → `folio_core` | ✓ |
| `folio_chat.*` → `folio_mcp` (as library) | ✓ |
| any `*.core.*` → `*.shell.*` | ✗ |
| `folio-core` → any other workspace pkg | ✗ |

## Infrastructure

Both `folio-sync` and `folio-mcp` run as docker-compose services (Lambda removed).

infra/ collects docker/, migrations/, seed/, and infrastructure scripts.

## Test Strategy

| Layer | Test type | Mock policy |
|-------|-----------|-------------|
| `folio_core` | Unit | No mocks |
| `folio_sync/core/` | Unit | No mocks |
| `folio_sync/shell/` | Integration | Mock boto3, psycopg connection factory |
| `folio_mcp/core/` | Unit | Assert SQL strings + Pydantic outputs |
| `folio_mcp/shell/` | Integration | Real DB |
| `folio_chat/` | Integration | Mock MCP client |
SPEC
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-05-26-repo-reorganization-design.md
git commit -m "docs: add repo reorganization design spec"
```

---

## Task 2: folio-sync core/ — move parser, hasher, categorizer

**Files:**
- Create: `packages/doc-sync/src/folio_sync/core/__init__.py`
- Create: `packages/doc-sync/src/folio_sync/core/parser.py`
- Create: `packages/doc-sync/src/folio_sync/core/hasher.py`
- Create: `packages/doc-sync/src/folio_sync/core/categorizer.py`
- Create: `packages/doc-sync/tests/folio_sync/core/__init__.py`
- Create: `packages/doc-sync/tests/folio_sync/core/test_parser.py`
- Create: `packages/doc-sync/tests/folio_sync/core/test_hasher.py`
- Create: `packages/doc-sync/tests/folio_sync/core/test_categorizer.py`

- [ ] **Step 1: Write failing tests at new import paths**

`packages/doc-sync/tests/folio_sync/core/__init__.py` — empty file.

`packages/doc-sync/tests/folio_sync/core/test_parser.py`:
```python
from folio_sync.core.parser import parse_markdown


def test_parse_markdown_with_valid_front_matter():
    parsed = parse_markdown("---\ntitle: test\n---\n# body")
    assert parsed.front_matter == {"title": "test"}
    assert parsed.body == "# body"


def test_parse_markdown_without_front_matter():
    parsed = parse_markdown("# Just body\nline 2")
    assert parsed.front_matter == {}
    assert parsed.body == "# Just body\nline 2"


def test_parse_markdown_with_invalid_yaml():
    content = "---\ntitle: : : invalid\n---\n# body"
    parsed = parse_markdown(content)
    assert parsed.front_matter == {}
    assert parsed.body == content


def test_parse_markdown_empty_file():
    parsed = parse_markdown("")
    assert parsed.front_matter == {}
    assert parsed.body == ""


def test_parse_markdown_empty_front_matter():
    parsed = parse_markdown("---\n---\n# body")
    assert parsed.front_matter == {}
    assert parsed.body == "# body"
```

`packages/doc-sync/tests/folio_sync/core/test_hasher.py`:
```python
import hashlib
from folio_sync.core.hasher import content_hash


def test_content_hash():
    content = "hello world"
    expected = hashlib.sha256(content.encode()).hexdigest()
    assert content_hash(content) == expected


def test_content_hash_empty():
    assert content_hash("") == hashlib.sha256(b"").hexdigest()
```

`packages/doc-sync/tests/folio_sync/core/test_categorizer.py`:
```python
from folio_sync.core.categorizer import (
    infer_category,
    infer_description,
    infer_slug,
    infer_sort_order,
    infer_title,
)


def test_infer_category_concepts():
    assert infer_category("content/en/docs/concepts/workloads/pods.md") == "concept"


def test_infer_category_tasks():
    assert infer_category("content/en/docs/tasks/run-application.md") == "task"


def test_infer_category_unknown():
    assert infer_category("random/path/doc.md") == "general"


def test_infer_category_adrs():
    assert infer_category("docs/adrs/001-use-postgres.md") == "adr"


def test_infer_slug_from_front_matter():
    assert infer_slug("some/path/file.md", {"topic_slug": "my-slug"}) == "my-slug"


def test_infer_slug_from_path():
    assert infer_slug("some/path/my-doc.md", {}) == "my-doc"


def test_infer_title_from_front_matter():
    assert infer_title("p.md", {"title": "My Title"}, "") == "My Title"


def test_infer_title_from_h1():
    assert infer_title("p.md", {}, "# Heading\n\nBody") == "Heading"


def test_infer_title_from_stem():
    assert infer_title("path/my-doc.md", {}, "no heading") == "My Doc"


def test_infer_description_from_front_matter():
    assert infer_description({"description": "My desc"}, "") == "My desc"


def test_infer_description_from_body():
    assert infer_description({}, "# Heading\n\nFirst paragraph.") == "First paragraph."


def test_infer_sort_order_from_weight():
    assert infer_sort_order("p.md", {"weight": 42}) == 42


def test_infer_sort_order_default():
    assert infer_sort_order("p.md", {}) == 0
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest packages/doc-sync/tests/folio_sync/core/ -v
```
Expected: `ModuleNotFoundError: No module named 'folio_sync.core'`

- [ ] **Step 3: Create core/__init__.py**

`packages/doc-sync/src/folio_sync/core/__init__.py` — empty.

- [ ] **Step 4: Create core/parser.py**

`packages/doc-sync/src/folio_sync/core/parser.py`:
```python
"""Markdown parsing with YAML front matter. Pure, without I/O."""

import yaml

from folio_core.models import ParsedMarkdown


def parse_markdown(raw: str) -> ParsedMarkdown:
    """Separates YAML front matter from the markdown body."""
    if not raw or not raw.startswith("---\n"):
        return ParsedMarkdown(front_matter={}, body=raw or "")
    try:
        _, fm_yaml, body = raw.split("---\n", 2)
        fm = yaml.safe_load(fm_yaml) or {}
        return ParsedMarkdown(front_matter=fm, body=body.lstrip())
    except (ValueError, yaml.YAMLError):
        return ParsedMarkdown(front_matter={}, body=raw)
```

- [ ] **Step 5: Create core/hasher.py**

`packages/doc-sync/src/folio_sync/core/hasher.py`:
```python
"""Content hashing. Pure, without I/O."""

import hashlib


def content_hash(raw: str) -> str:
    """SHA-256 of the raw content."""
    return hashlib.sha256(raw.encode()).hexdigest()
```

- [ ] **Step 6: Create core/categorizer.py**

Copy `packages/core/src/folio_core/categorizer.py` verbatim to `packages/doc-sync/src/folio_sync/core/categorizer.py` (file has no imports from folio_core, only stdlib `pathlib`).

```bash
cp packages/core/src/folio_core/categorizer.py packages/doc-sync/src/folio_sync/core/categorizer.py
```

- [ ] **Step 7: Run — expect PASS**

```bash
uv run pytest packages/doc-sync/tests/folio_sync/core/ -v
```
Expected: all green.

- [ ] **Step 8: Verify folio-core tests still pass (parser/hasher/categorizer still live there)**

```bash
uv run pytest packages/core/tests/ -v
```
Expected: all green (old files not deleted yet).

- [ ] **Step 9: Commit**

```bash
git add packages/doc-sync/src/folio_sync/core/ packages/doc-sync/tests/folio_sync/core/
git commit -m "feat(sync): add core/ subpackage with parser, hasher, categorizer"
```

---

## Task 3: folio-sync/core/indexer.py — pure prepare_document

**Files:**
- Create: `packages/doc-sync/src/folio_sync/core/indexer.py`
- Create: `packages/doc-sync/tests/folio_sync/core/test_indexer.py`

- [ ] **Step 1: Write failing test**

`packages/doc-sync/tests/folio_sync/core/test_indexer.py`:
```python
"""Tests for folio_sync/core/indexer.py — pure document preparation."""

from folio_sync.core.indexer import prepare_document

_RAW = "---\ntitle: Pods\ntags:\n  - concept\n---\n# Pods\n\nPods are the smallest units."


def test_prepare_document_returns_expected_fields():
    doc = prepare_document("content/en/docs/concepts/pods.md", _RAW)

    assert doc["path"] == "content/en/docs/concepts/pods.md"
    assert doc["title"] == "Pods"
    assert doc["content"] == "# Pods\n\nPods are the smallest units."
    assert len(doc["content_hash"]) == 64  # SHA-256 hex
    assert doc["slug"] == "pods"
    assert doc["category"] == "concept"
    assert "units" in doc["description"]
    assert doc["sort_order"] == 0
    assert doc["metadata"] == '{"tags": ["concept"]}'


def test_prepare_document_no_front_matter():
    doc = prepare_document("random/note.md", "# Note\n\nSome text.")
    assert doc["title"] == "Note"
    assert doc["category"] == "general"
    assert doc["metadata"] == '{"tags": []}'


def test_prepare_document_hash_changes_with_content():
    doc1 = prepare_document("p.md", "content A")
    doc2 = prepare_document("p.md", "content B")
    assert doc1["content_hash"] != doc2["content_hash"]
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest packages/doc-sync/tests/folio_sync/core/test_indexer.py -v
```
Expected: `ImportError: cannot import name 'prepare_document'`

- [ ] **Step 3: Implement core/indexer.py**

`packages/doc-sync/src/folio_sync/core/indexer.py`:
```python
"""Pure document preparation. No I/O — returns a dict ready for DB upsert."""

import json

from folio_sync.core.categorizer import (
    infer_category,
    infer_description,
    infer_slug,
    infer_sort_order,
    infer_title,
)
from folio_sync.core.hasher import content_hash
from folio_sync.core.parser import parse_markdown


def prepare_document(path: str, raw: str) -> dict:
    """Derive all indexable fields from a raw markdown string.

    Returns a dict with keys: path, content, content_hash, title, slug,
    category, description, sort_order, metadata (JSON string).
    """
    parsed = parse_markdown(raw)
    h = content_hash(raw)
    fm = parsed.front_matter
    return {
        "path": path,
        "content": parsed.body,
        "content_hash": h,
        "title": infer_title(path, fm, parsed.body),
        "slug": infer_slug(path, fm),
        "category": infer_category(path),
        "description": infer_description(fm, parsed.body),
        "sort_order": infer_sort_order(path, fm),
        "metadata": json.dumps({"tags": fm.get("tags", [])}),
    }
```

- [ ] **Step 4: Run — expect PASS**

```bash
uv run pytest packages/doc-sync/tests/folio_sync/core/ -v
```
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add packages/doc-sync/src/folio_sync/core/indexer.py \
        packages/doc-sync/tests/folio_sync/core/test_indexer.py
git commit -m "feat(sync): add core/indexer.py with pure prepare_document"
```

---

## Task 4: folio-sync/shell/ subpackage

**Files:**
- Create: `packages/doc-sync/src/folio_sync/shell/__init__.py`
- Create: `packages/doc-sync/src/folio_sync/shell/config.py`
- Create: `packages/doc-sync/src/folio_sync/shell/db.py`
- Create: `packages/doc-sync/src/folio_sync/shell/s3_client.py`
- Create: `packages/doc-sync/src/folio_sync/shell/indexer.py`
- Create: `packages/doc-sync/src/folio_sync/shell/handler.py`
- Create: `packages/doc-sync/tests/folio_sync/shell/__init__.py`
- Create: `packages/doc-sync/tests/folio_sync/shell/test_indexer.py`
- Create: `packages/doc-sync/tests/folio_sync/shell/test_handler.py`
- Modify: `packages/doc-sync/pyproject.toml` (scripts entry point)

- [ ] **Step 1: Create shell/__init__.py** — empty.

- [ ] **Step 2: Copy config, db, s3_client verbatim**

```bash
cp packages/doc-sync/src/folio_sync/config.py packages/doc-sync/src/folio_sync/shell/config.py
cp packages/doc-sync/src/folio_sync/db.py packages/doc-sync/src/folio_sync/shell/db.py
cp packages/doc-sync/src/folio_sync/s3_client.py packages/doc-sync/src/folio_sync/shell/s3_client.py
```

Update the one internal import in `shell/config.py` — check if it imports from `folio_sync` (it doesn't; it only imports dynaconf). Same for db and s3_client. They only import from stdlib, psycopg, boto3, and structlog — no changes needed.

- [ ] **Step 3: Write failing test for shell/indexer.py**

`packages/doc-sync/tests/folio_sync/shell/__init__.py` — empty.

`packages/doc-sync/tests/folio_sync/shell/test_indexer.py`:
```python
"""Tests for folio_sync/shell/indexer.py — DB upsert logic."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from folio_sync.shell.indexer import full_sync, upsert_document

_PREPARED = {
    "path": "concepts/pods.md",
    "content": "# Pods\n\nPods are units.",
    "content_hash": "abc123",
    "title": "Pods",
    "slug": "pods",
    "category": "concept",
    "description": "Pods are units.",
    "sort_order": 0,
    "metadata": '{"tags": []}',
}


@pytest.fixture
def mock_cursor():
    cursor = AsyncMock()
    cursor.__aenter__ = AsyncMock(return_value=cursor)
    cursor.__aexit__ = AsyncMock(return_value=False)
    return cursor


@pytest.fixture
def mock_conn(mock_cursor):
    connection = AsyncMock()
    connection.__aenter__ = AsyncMock(return_value=connection)
    connection.__aexit__ = AsyncMock(return_value=False)
    connection.cursor = MagicMock(return_value=mock_cursor)
    return connection


@pytest.fixture
def mock_conn_ctx(mock_conn):
    @asynccontextmanager
    async def _conn():
        yield mock_conn
    return _conn


async def test_upsert_indexes_new_doc(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = None  # no existing hash

    with (
        patch("folio_sync.shell.indexer.conn", mock_conn_ctx),
        patch("folio_sync.shell.indexer.prepare_document", return_value=_PREPARED),
    ):
        changed = await upsert_document("concepts/pods.md", "raw")

    assert changed is True
    assert mock_cursor.execute.call_count == 3  # hash check + doc upsert + topic upsert


async def test_upsert_skips_unchanged_doc(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = ("abc123",)  # hash matches

    with (
        patch("folio_sync.shell.indexer.conn", mock_conn_ctx),
        patch("folio_sync.shell.indexer.prepare_document", return_value=_PREPARED),
    ):
        changed = await upsert_document("concepts/pods.md", "raw")

    assert changed is False
    assert mock_cursor.execute.call_count == 1  # only hash check


async def test_upsert_updates_changed_doc(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = ("old_hash",)  # different hash

    with (
        patch("folio_sync.shell.indexer.conn", mock_conn_ctx),
        patch("folio_sync.shell.indexer.prepare_document", return_value=_PREPARED),
    ):
        changed = await upsert_document("concepts/pods.md", "raw")

    assert changed is True


async def test_full_sync_reports_stats():
    docs = [("concepts/pods.md", "raw1"), ("concepts/services.md", "raw2")]

    async def _iter(bucket, prefix):
        for key, content in docs:
            yield key, content

    with (
        patch("folio_sync.shell.indexer.iter_markdowns", _iter),
        patch("folio_sync.shell.indexer.upsert_document", AsyncMock(side_effect=[True, False])),
    ):
        stats = await full_sync()

    assert stats == {"scanned": 2, "indexed": 1, "skipped": 1}
```

- [ ] **Step 4: Run — expect FAIL**

```bash
uv run pytest packages/doc-sync/tests/folio_sync/shell/ -v
```
Expected: `ModuleNotFoundError: No module named 'folio_sync.shell.indexer'`

- [ ] **Step 5: Implement shell/indexer.py**

`packages/doc-sync/src/folio_sync/shell/indexer.py`:
```python
"""I/O layer: reads from S3, writes to Postgres. Calls core/indexer.py."""

import structlog

from folio_core import postgres_sql
from folio_sync.core.indexer import prepare_document
from folio_sync.shell.config import settings
from folio_sync.shell.db import conn
from folio_sync.shell.s3_client import iter_markdowns

logger = structlog.get_logger()


async def upsert_document(path: str, raw: str) -> bool:
    """Index a document. Returns True if the document changed."""
    doc = prepare_document(path, raw)

    async with conn() as c:
        async with c.cursor() as cur:
            await cur.execute(
                *postgres_sql(t"SELECT content_hash FROM documents WHERE path = {doc['path']}")
            )
            row = await cur.fetchone()
            if row and row[0] == doc["content_hash"]:
                return False

            await cur.execute(
                *postgres_sql(t"""
                INSERT INTO documents (path, title, content, content_hash, metadata)
                VALUES ({doc['path']}, {doc['title']}, {doc['content']},
                        {doc['content_hash']}, {doc['metadata']}::jsonb)
                ON CONFLICT (path) DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    content_hash = EXCLUDED.content_hash,
                    metadata = EXCLUDED.metadata,
                    updated_at = now()
                """)
            )

            await cur.execute(
                *postgres_sql(t"""
                INSERT INTO topics (slug, title, description, category, doc_path, sort_order)
                VALUES ({doc['slug']}, {doc['title']}, {doc['description']},
                        {doc['category']}, {doc['path']}, {doc['sort_order']})
                ON CONFLICT (slug) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    category = EXCLUDED.category,
                    doc_path = EXCLUDED.doc_path,
                    sort_order = EXCLUDED.sort_order,
                    updated_at = now()
                """)
            )

        await c.commit()

    logger.info("doc.indexed", path=path)
    return True


async def full_sync() -> dict:
    """Sync all documents from S3. Returns stats dict."""
    stats = {"scanned": 0, "indexed": 0, "skipped": 0}
    async for key, content in iter_markdowns(settings.s3.bucket, settings.s3.prefix):
        stats["scanned"] += 1
        changed = await upsert_document(key, content)
        if changed:
            stats["indexed"] += 1
        else:
            stats["skipped"] += 1
    logger.info("sync.full_complete", **stats)
    return stats
```

- [ ] **Step 6: Write failing test for shell/handler.py**

`packages/doc-sync/tests/folio_sync/shell/test_handler.py`:
```python
"""Tests for folio_sync/shell/handler.py — CLI entry point."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from folio_sync.shell.handler import main


def test_main_runs_full_sync(capsys):
    with patch("folio_sync.shell.handler.full_sync", AsyncMock(return_value={"scanned": 0, "indexed": 0, "skipped": 0})):
        with patch("folio_sync.shell.handler.close_pool", AsyncMock()):
            main()
```

- [ ] **Step 7: Run — expect FAIL**

```bash
uv run pytest packages/doc-sync/tests/folio_sync/shell/test_handler.py -v
```
Expected: `ModuleNotFoundError: No module named 'folio_sync.shell.handler'`

- [ ] **Step 8: Implement shell/handler.py**

`packages/doc-sync/src/folio_sync/shell/handler.py`:
```python
"""CLI entry point for the doc-sync service."""

import asyncio

import structlog

from folio_sync.shell.db import close_pool
from folio_sync.shell.indexer import full_sync

logger = structlog.get_logger()


async def _run() -> None:
    stats = await full_sync()
    await close_pool()
    logger.info("sync.cli_complete", **stats)


def main() -> None:
    """CLI entry point — runs a full S3→Postgres sync."""
    asyncio.run(_run())
```

- [ ] **Step 9: Update scripts entry point in pyproject.toml**

`packages/doc-sync/pyproject.toml` — change:
```toml
[project.scripts]
folio-sync = "folio_sync.shell.handler:main"
```

- [ ] **Step 10: Run all shell tests — expect PASS**

```bash
uv run pytest packages/doc-sync/tests/folio_sync/shell/ -v
```
Expected: all green.

- [ ] **Step 11: Verify old flat-module tests still pass (not deleted yet)**

```bash
uv run pytest packages/doc-sync/tests/ -v
```
Expected: all green (both old and new tests pass simultaneously).

- [ ] **Step 12: Commit**

```bash
git add packages/doc-sync/src/folio_sync/shell/ \
        packages/doc-sync/tests/folio_sync/shell/ \
        packages/doc-sync/pyproject.toml
git commit -m "feat(sync): add shell/ subpackage with db, s3_client, indexer, handler"
```

---

## Task 5: folio-sync cleanup — remove old flat modules

**Files:**
- Delete: `packages/doc-sync/src/folio_sync/config.py`
- Delete: `packages/doc-sync/src/folio_sync/db.py`
- Delete: `packages/doc-sync/src/folio_sync/s3_client.py`
- Delete: `packages/doc-sync/src/folio_sync/indexer.py`
- Delete: `packages/doc-sync/src/folio_sync/handler.py`
- Delete: `packages/doc-sync/tests/folio_sync/test_indexer.py`
- Delete: `packages/doc-sync/tests/folio_sync/test_sync_handler.py`
- Modify: `packages/doc-sync/tests/integration/test_e2e.py`

- [ ] **Step 1: Delete old flat modules**

```bash
rm packages/doc-sync/src/folio_sync/config.py \
   packages/doc-sync/src/folio_sync/db.py \
   packages/doc-sync/src/folio_sync/s3_client.py \
   packages/doc-sync/src/folio_sync/indexer.py \
   packages/doc-sync/src/folio_sync/handler.py
```

- [ ] **Step 2: Delete old flat tests**

```bash
rm packages/doc-sync/tests/folio_sync/test_indexer.py \
   packages/doc-sync/tests/folio_sync/test_sync_handler.py
```

- [ ] **Step 3: Update integration test imports**

`packages/doc-sync/tests/integration/test_e2e.py` — update the two imports:
```python
async def test_full_sync_indexes_s3_docs():
    from folio_sync.shell.db import close_pool, conn
    from folio_sync.shell.indexer import full_sync
    # ... rest unchanged
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest packages/doc-sync/tests/ -m "not integration" -v
```
Expected: all green (only shell/ and core/ tests run).

- [ ] **Step 5: Commit**

```bash
git add -u packages/doc-sync/
git commit -m "refactor(sync): remove old flat modules, keep only core/ and shell/"
```

---

## Task 6: folio-core cleanup — remove parser, hasher, categorizer

**Files:**
- Delete: `packages/core/src/folio_core/parser.py`
- Delete: `packages/core/src/folio_core/hasher.py`
- Delete: `packages/core/src/folio_core/categorizer.py`
- Delete: `packages/core/tests/folio_core/test_parser.py`
- Delete: `packages/core/tests/folio_core/test_hasher.py`
- Delete: `packages/core/tests/folio_core/test_categorizer.py`
- Modify: `packages/core/src/folio_core/__init__.py`
- Modify: `packages/core/pyproject.toml`

- [ ] **Step 1: Delete moved files**

```bash
rm packages/core/src/folio_core/parser.py \
   packages/core/src/folio_core/hasher.py \
   packages/core/src/folio_core/categorizer.py \
   packages/core/tests/folio_core/test_parser.py \
   packages/core/tests/folio_core/test_hasher.py \
   packages/core/tests/folio_core/test_categorizer.py
```

- [ ] **Step 2: Update folio_core/__init__.py**

`packages/core/src/folio_core/__init__.py`:
```python
"""Shared domain types and SQL helpers for the folio workspace."""

__version__ = "0.1.0"

from .sql import postgres_sql as postgres_sql
```
(Remove any exports of parser/hasher/categorizer if present — they weren't exported, only `postgres_sql` was.)

- [ ] **Step 3: Drop pyyaml from folio-core dependencies**

`packages/core/pyproject.toml` — remove `"pyyaml>=6.0.3"` from `dependencies`. Add it to folio-sync instead:

```bash
# In folio-sync:
uv add --package folio-sync pyyaml
```

- [ ] **Step 4: Run all tests — expect PASS**

```bash
uv run pytest packages/core/tests/ packages/doc-sync/tests/ -m "not integration" -v
```
Expected: all green. folio-core tests only cover `test_sql.py` and `test_models.py` (if any).

- [ ] **Step 5: Commit**

```bash
git add -u packages/core/ packages/doc-sync/
git commit -m "refactor(core): remove parser/hasher/categorizer — moved to folio-sync/core"
```

---

## Task 7: folio-mcp/core/ — queries.py and mappers.py

**Files:**
- Create: `packages/mcp-server/src/folio_mcp/core/__init__.py`
- Create: `packages/mcp-server/src/folio_mcp/core/queries.py`
- Create: `packages/mcp-server/src/folio_mcp/core/mappers.py`
- Create: `packages/mcp-server/tests/folio_mcp/core/__init__.py`
- Create: `packages/mcp-server/tests/folio_mcp/core/test_queries.py`
- Create: `packages/mcp-server/tests/folio_mcp/core/test_mappers.py`

- [ ] **Step 1: Write failing tests for queries.py**

`packages/mcp-server/tests/folio_mcp/core/__init__.py` — empty.

`packages/mcp-server/tests/folio_mcp/core/test_queries.py`:
```python
"""Tests for folio_mcp/core/queries.py — pure SQL builders."""

from folio_mcp.core.queries import get_document_sql, list_topics_sql, search_docs_sql


def test_search_docs_sql_returns_string():
    sql = search_docs_sql(max_fragments=3, max_words=25)
    assert isinstance(sql, str)
    assert "tsv @@ q" in sql
    assert "MaxFragments=3" in sql
    assert "MaxWords=25" in sql
    assert "%s" in sql  # for query param
    assert sql.count("%s") == 2  # query + limit


def test_search_docs_sql_different_config():
    sql1 = search_docs_sql(max_fragments=1, max_words=10)
    sql2 = search_docs_sql(max_fragments=5, max_words=50)
    assert "MaxFragments=1" in sql1
    assert "MaxFragments=5" in sql2


def test_list_topics_sql_no_category():
    sql, params = list_topics_sql(None)
    assert "FROM topics" in sql
    assert "WHERE category" not in sql
    assert params == ()


def test_list_topics_sql_with_category():
    sql, params = list_topics_sql("concept")
    assert "WHERE category = %s" in sql
    assert params == ("concept",)


def test_get_document_sql():
    sql = get_document_sql()
    assert "FROM documents WHERE path = %s" in sql
    assert "path, title, content, metadata" in sql
```

- [ ] **Step 2: Run — expect FAIL**

```bash
uv run pytest packages/mcp-server/tests/folio_mcp/core/test_queries.py -v
```
Expected: `ModuleNotFoundError: No module named 'folio_mcp.core'`

- [ ] **Step 3: Create core/__init__.py** — empty.

- [ ] **Step 4: Implement core/queries.py**

`packages/mcp-server/src/folio_mcp/core/queries.py`:
```python
"""Pure SQL query builders. No I/O — return (sql_string, params) tuples."""

from typing import LiteralString, cast


def search_docs_sql(max_fragments: int, max_words: int) -> LiteralString:
    """Return parameterized BM25 search SQL. Bind params: (query, limit)."""
    return cast(
        LiteralString,
        f"""
        SELECT
            path, title,
            ts_rank_cd(tsv, q) AS rank,
            ts_headline('simple', content, q,
                'StartSel=<mark>, StopSel=</mark>, '
                'MaxFragments={max_fragments}, '
                'MaxWords={max_words}, MinWords=10'
            ) AS snippet
        FROM documents,
             websearch_to_tsquery('simple', %s) AS q
        WHERE tsv @@ q
        ORDER BY rank DESC
        LIMIT %s
        """,
    )


def list_topics_sql(category: str | None) -> tuple[str, tuple]:
    """Return (sql, params) for listing topics, optionally filtered by category."""
    if category:
        return (
            "SELECT slug, title, description, category, doc_path, sort_order"
            " FROM topics WHERE category = %s ORDER BY category, sort_order, title",
            (category,),
        )
    return (
        "SELECT slug, title, description, category, doc_path, sort_order"
        " FROM topics ORDER BY category, sort_order, title",
        (),
    )


def get_document_sql() -> str:
    """Return SQL for fetching a single document by path. Bind param: (path,)."""
    return "SELECT path, title, content, metadata FROM documents WHERE path = %s"
```

- [ ] **Step 5: Run queries tests — expect PASS**

```bash
uv run pytest packages/mcp-server/tests/folio_mcp/core/test_queries.py -v
```

- [ ] **Step 6: Write failing tests for mappers.py**

`packages/mcp-server/tests/folio_mcp/core/test_mappers.py`:
```python
"""Tests for folio_mcp/core/mappers.py — pure row-to-Pydantic mappers."""

from folio_mcp.core.mappers import map_document_row, map_search_rows, map_topic_rows

_SEARCH_ROWS = [
    ("concepts/pods.md", "Pods", 0.75, "Pods are the <mark>smallest</mark> units."),
    ("concepts/services.md", "Services", 0.50, "Services <mark>expose</mark> pods."),
]

_TOPIC_ROWS = [
    ("pods-overview", "Pods Overview", "Pods are units.", "concept", "concepts/pods.md", 10),
    ("run-app", "Run Application", "Deploy an app.", "task", "tasks/run-app.md", 5),
]

_DOCUMENT_ROW = ("concepts/pods.md", "Pods", "# Pods\n\nContent.", {"tags": ["concept"]})


def test_map_search_rows_returns_result():
    result = map_search_rows(_SEARCH_ROWS, "pods")
    assert result.query == "pods"
    assert len(result.matches) == 2
    assert result.matches[0].path == "concepts/pods.md"
    assert result.matches[0].rank == 0.75
    assert "<mark>" in result.matches[0].snippet


def test_map_search_rows_empty():
    result = map_search_rows([], "nothing")
    assert result.matches == []
    assert result.query == "nothing"


def test_map_topic_rows():
    result = map_topic_rows(_TOPIC_ROWS)
    assert result.total == 2
    assert result.topics[0].slug == "pods-overview"
    assert result.topics[1].category == "task"


def test_map_document_row_found():
    result = map_document_row(_DOCUMENT_ROW)
    assert result is not None
    assert result.path == "concepts/pods.md"
    assert result.title == "Pods"
    assert result.metadata == {"tags": ["concept"]}


def test_map_document_row_not_found():
    assert map_document_row(None) is None
```

- [ ] **Step 7: Run — expect FAIL**

```bash
uv run pytest packages/mcp-server/tests/folio_mcp/core/test_mappers.py -v
```
Expected: `ImportError: cannot import name 'map_document_row'`

- [ ] **Step 8: Implement core/mappers.py**

`packages/mcp-server/src/folio_mcp/core/mappers.py`:
```python
"""Pure mappers: DB rows → Pydantic models. No I/O."""

from folio_core.models import (
    GetDocumentResult,
    ListTopicsResult,
    SearchDocsResult,
    SearchMatch,
    Topic,
)


def map_search_rows(rows: list, query: str) -> SearchDocsResult:
    """Map raw DB rows from search_docs query to SearchDocsResult."""
    matches = [
        SearchMatch(path=r[0], title=r[1], rank=float(r[2]), snippet=r[3]) for r in rows
    ]
    return SearchDocsResult(matches=matches, query=query)


def map_topic_rows(rows: list) -> ListTopicsResult:
    """Map raw DB rows from list_topics query to ListTopicsResult."""
    topics = [
        Topic(slug=r[0], title=r[1], description=r[2], category=r[3], doc_path=r[4], sort_order=r[5])
        for r in rows
    ]
    return ListTopicsResult(topics=topics, total=len(topics))


def map_document_row(row: tuple | None) -> GetDocumentResult | None:
    """Map a single DB row from get_document query to GetDocumentResult."""
    if row is None:
        return None
    return GetDocumentResult(path=row[0], title=row[1], content=row[2], metadata=row[3])
```

- [ ] **Step 9: Run all mcp core tests — expect PASS**

```bash
uv run pytest packages/mcp-server/tests/folio_mcp/core/ -v
```

- [ ] **Step 10: Commit**

```bash
git add packages/mcp-server/src/folio_mcp/core/ \
        packages/mcp-server/tests/folio_mcp/core/
git commit -m "feat(mcp): add core/ subpackage with queries and mappers"
```

---

## Task 8: folio-mcp/shell/ subpackage

**Files:**
- Create: `packages/mcp-server/src/folio_mcp/shell/__init__.py`
- Create: `packages/mcp-server/src/folio_mcp/shell/config.py`
- Create: `packages/mcp-server/src/folio_mcp/shell/db.py`
- Create: `packages/mcp-server/src/folio_mcp/shell/tools/__init__.py`
- Create: `packages/mcp-server/src/folio_mcp/shell/tools/search_docs.py`
- Create: `packages/mcp-server/src/folio_mcp/shell/tools/list_topics.py`
- Create: `packages/mcp-server/src/folio_mcp/shell/tools/get_document.py`
- Create: `packages/mcp-server/src/folio_mcp/shell/handler.py`
- Create: `packages/mcp-server/tests/folio_mcp/shell/__init__.py`
- Create: `packages/mcp-server/tests/folio_mcp/shell/test_search_docs.py`
- Create: `packages/mcp-server/tests/folio_mcp/shell/test_list_topics.py`
- Create: `packages/mcp-server/tests/folio_mcp/shell/test_get_document.py`
- Create: `packages/mcp-server/tests/folio_mcp/shell/test_mcp_handler.py`
- Modify: `packages/mcp-server/pyproject.toml`

- [ ] **Step 1: Create shell/ and shell/tools/ empty __init__.py files** — all empty.

- [ ] **Step 2: Copy config and db verbatim**

```bash
cp packages/mcp-server/src/folio_mcp/config.py packages/mcp-server/src/folio_mcp/shell/config.py
cp packages/mcp-server/src/folio_mcp/db.py packages/mcp-server/src/folio_mcp/shell/db.py
```

Update internal import in `shell/db.py`: change `from folio_mcp.config import settings` to `from folio_mcp.shell.config import settings`.

- [ ] **Step 3: Write failing tests for shell tools**

`packages/mcp-server/tests/folio_mcp/shell/__init__.py` — empty.

`packages/mcp-server/tests/folio_mcp/shell/test_search_docs.py`:
```python
from unittest.mock import patch

import pytest
from folio_mcp.shell.tools.search_docs import search_docs

_ROWS = [
    ("concepts/pods.md", "Pods", 0.75, "Pods are the <mark>smallest</mark> units."),
    ("concepts/services.md", "Services", 0.50, "Services <mark>expose</mark> pods."),
]


async def test_search_docs_returns_ranked_matches(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = _ROWS

    with patch("folio_mcp.shell.tools.search_docs.conn", mock_conn_ctx):
        result = await search_docs("pods scheduling")

    assert result.query == "pods scheduling"
    assert len(result.matches) == 2
    assert result.matches[0].rank == pytest.approx(0.75)


async def test_search_docs_empty_results(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = []

    with patch("folio_mcp.shell.tools.search_docs.conn", mock_conn_ctx):
        result = await search_docs("xyznonexistent")

    assert result.matches == []


async def test_search_docs_clamps_limit(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = []

    with patch("folio_mcp.shell.tools.search_docs.conn", mock_conn_ctx):
        await search_docs("pods", limit=9999)

    params = mock_cursor.execute.call_args.args[1]
    assert params[-1] <= 50


async def test_search_docs_minimum_limit(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = []

    with patch("folio_mcp.shell.tools.search_docs.conn", mock_conn_ctx):
        await search_docs("pods", limit=0)

    params = mock_cursor.execute.call_args.args[1]
    assert params[-1] >= 1
```

`packages/mcp-server/tests/folio_mcp/shell/test_list_topics.py`:
```python
from unittest.mock import patch

from folio_mcp.shell.tools.list_topics import list_topics

_ROWS = [
    ("pods-overview", "Pods Overview", "Pods are units.", "concept", "concepts/pods.md", 10),
    ("services", "Services", "Services expose pods.", "concept", "concepts/services.md", 20),
    ("run-app", "Run Application", "Deploy an app.", "task", "tasks/run-app.md", 5),
]


async def test_list_topics_all(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = _ROWS

    with patch("folio_mcp.shell.tools.list_topics.conn", mock_conn_ctx):
        result = await list_topics()

    assert result.total == 3
    assert result.topics[0].slug == "pods-overview"


async def test_list_topics_filtered(mock_conn_ctx, mock_cursor):
    concept_rows = [r for r in _ROWS if r[3] == "concept"]
    mock_cursor.fetchall.return_value = concept_rows

    with patch("folio_mcp.shell.tools.list_topics.conn", mock_conn_ctx):
        result = await list_topics(category="concept")

    assert result.total == 2
    params = mock_cursor.execute.call_args.args[1]
    assert "concept" in params


async def test_list_topics_empty(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchall.return_value = []

    with patch("folio_mcp.shell.tools.list_topics.conn", mock_conn_ctx):
        result = await list_topics()

    assert result.total == 0
```

`packages/mcp-server/tests/folio_mcp/shell/test_get_document.py`:
```python
from unittest.mock import patch

from folio_mcp.shell.tools.get_document import get_document

_ROW = ("concepts/pods.md", "Pods", "# Pods\n\nPods are units.", {"tags": ["concept"]})


async def test_get_document_found(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = _ROW

    with patch("folio_mcp.shell.tools.get_document.conn", mock_conn_ctx):
        result = await get_document("concepts/pods.md")

    assert result is not None
    assert result.path == "concepts/pods.md"
    assert result.metadata == {"tags": ["concept"]}


async def test_get_document_not_found(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = None

    with patch("folio_mcp.shell.tools.get_document.conn", mock_conn_ctx):
        result = await get_document("nonexistent.md")

    assert result is None
```

`packages/mcp-server/tests/folio_mcp/shell/test_mcp_handler.py`:
```python
import pytest
from folio_mcp.shell.handler import mcp


@pytest.mark.asyncio
async def test_mcp_instance():
    assert mcp.name == "folio"
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "list_topics" in tool_names
    assert "search_docs" in tool_names
    assert "get_document" in tool_names
```

- [ ] **Step 4: Run — expect FAIL**

```bash
uv run pytest packages/mcp-server/tests/folio_mcp/shell/ -v
```
Expected: `ModuleNotFoundError: No module named 'folio_mcp.shell.tools'`

- [ ] **Step 5: Implement shell/tools/search_docs.py**

`packages/mcp-server/src/folio_mcp/shell/tools/search_docs.py`:
```python
"""Tool: search_docs. BM25 via Postgres FTS."""

from folio_core.models import SearchDocsResult
from folio_mcp.core.mappers import map_search_rows
from folio_mcp.core.queries import search_docs_sql
from folio_mcp.shell.config import settings
from folio_mcp.shell.db import conn


async def search_docs(query: str, limit: int = 10) -> SearchDocsResult:
    """Search documents by terms. Returns ranked paths and snippets.

    Use after list_topics to find specific content.
    Websearch syntax: "exact phrase", OR, -excluded.

    Args:
        query: Search terms. E.g., "scheduling pods affinity"
        limit: Maximum number of results (1-50).
    """
    limit = min(max(limit, 1), settings.search.max_limit)
    sql = search_docs_sql(
        max_fragments=settings.search.snippet_max_fragments,
        max_words=settings.search.snippet_max_words,
    )
    async with conn() as c, c.cursor() as cur:
        await cur.execute(sql, (query, limit))
        rows = await cur.fetchall()
    return map_search_rows(rows, query)
```

- [ ] **Step 6: Implement shell/tools/list_topics.py**

`packages/mcp-server/src/folio_mcp/shell/tools/list_topics.py`:
```python
"""Tool: list_topics."""

from folio_core.models import ListTopicsResult
from folio_mcp.core.mappers import map_topic_rows
from folio_mcp.core.queries import list_topics_sql
from folio_mcp.shell.db import conn


async def list_topics(category: str | None = None) -> ListTopicsResult:
    """Lists available topics in the documentation.

    Use first to discover the platform's internal vocabulary.

    Args:
        category: Filter by category (e.g., "concept", "task", "starter", "adr").
    """
    sql, params = list_topics_sql(category)
    async with conn() as c, c.cursor() as cur:
        await cur.execute(sql, params)
        rows = await cur.fetchall()
    return map_topic_rows(rows)
```

- [ ] **Step 7: Implement shell/tools/get_document.py**

`packages/mcp-server/src/folio_mcp/shell/tools/get_document.py`:
```python
"""Tool: get_document."""

from folio_core.models import GetDocumentResult
from folio_mcp.core.mappers import map_document_row
from folio_mcp.core.queries import get_document_sql
from folio_mcp.shell.db import conn


async def get_document(path: str) -> GetDocumentResult | None:
    """Returns the full markdown of a document.

    Use after search_docs to read the full content.

    Args:
        path: Document path, e.g., "concepts/workloads/pods.md"
    """
    sql = get_document_sql()
    async with conn() as c, c.cursor() as cur:
        await cur.execute(sql, (path,))
        row = await cur.fetchone()
    return map_document_row(row)
```

- [ ] **Step 8: Implement shell/handler.py**

`packages/mcp-server/src/folio_mcp/shell/handler.py` — copy the MCP registrations from the original `packages/mcp-server/src/folio_mcp/handler.py`, updating import paths to `folio_mcp.shell.*` and removing `lambda_handler`, `_invoke_tool`, and the `_loop` / `asyncio.set_event_loop` at module level:

```python
"""MCP server handler for folio."""

from fastmcp import FastMCP

from folio_mcp.shell.tools.get_document import get_document as get_document_impl
from folio_mcp.shell.tools.list_topics import list_topics as list_topics_impl
from folio_mcp.shell.tools.search_docs import search_docs as search_docs_impl

mcp = FastMCP(
    name="folio",
    instructions=(
        "[EN] This server is the authoritative source for ALL project documentation. "
        "You MUST use these tools — not filesystem tools (Read, Glob), skill files, "
        "or training data — to answer any question about this project's docs, architecture, "
        "or content. Even if the query matches a known skill or local file name, always call "
        "search_docs first to retrieve indexed knowledge-base content. "
        "Never answer from memory when these tools are available. "
        "Required flow: 1) list_topics to discover vocabulary, "
        "2) search_docs to find relevant documents, "
        "3) get_document to fetch full content. "
        "[PT-BR] Este servidor é a fonte autoritativa de TODA a documentação do projeto. "
        "DEVE usar estas ferramentas — não ferramentas de arquivo (Read, Glob), skill files "
        "nem dados de treino — "
        "para responder qualquer pergunta sobre docs, arquitetura ou conteúdo deste projeto. "
        "Mesmo que a query corresponda a um skill ou arquivo local conhecido, sempre chame "
        "search_docs primeiro para recuperar conteúdo indexado na base de conhecimento. "
        "Nunca responda da memória quando estas ferramentas estiverem disponíveis. "
        "Fluxo obrigatório: 1) list_topics para descobrir vocabulário, "
        "2) search_docs para encontrar documentos relevantes, "
        "3) get_document para buscar conteúdo completo."
    ),
)


@mcp.tool()
async def list_topics(category: str | None = None):
    """[EN] List available documentation topics. Use this to discover the internal vocabulary.

    ALWAYS use this tool to discover available documentation topics in the project.
    Never list files on the filesystem or use directory listing tools.

    [PT-BR] Lista os tópicos disponíveis na documentação.
    SEMPRE use esta ferramenta para descobrir os tópicos de documentação disponíveis.

    Args:
        category: Filter by category (e.g., "concept", "task", "starter", "adr").
    """
    return await list_topics_impl(category)


@mcp.tool()
async def search_docs(query: str, limit: int = 10):
    """[EN] Search the indexed knowledge-base documents by terms.

    ALWAYS use this tool to search — never use filesystem tools (Read, Glob, Grep).

    [PT-BR] Busca documentos indexados na base de conhecimento por termos.

    Args:
        query: Search terms.
        limit: Max results (1-50).
    """
    return await search_docs_impl(query, limit)


@mcp.tool()
async def get_document(path: str):
    """[EN] Fetch the complete indexed content of a knowledge-base document by its path.

    ALWAYS use this tool to read documents — never use filesystem tools (Read, Glob).

    [PT-BR] Obtém o conteúdo completo indexado de um documento da base de conhecimento.

    Args:
        path: Document path as returned by search_docs or list_topics.
    """
    return await get_document_impl(path)


def main() -> None:
    """CLI entry point — runs the MCP server over stdio transport."""
    mcp.run(transport="stdio")
```

- [ ] **Step 9: Update pyproject.toml scripts entry**

`packages/mcp-server/pyproject.toml`:
```toml
[project.scripts]
folio-mcp = "folio_mcp.shell.handler:main"
```

- [ ] **Step 10: Run all shell tests — expect PASS**

```bash
uv run pytest packages/mcp-server/tests/folio_mcp/shell/ -v
```
Expected: all green.

- [ ] **Step 11: Verify old flat-module tests still pass (not deleted yet)**

```bash
uv run pytest packages/mcp-server/tests/ -v
```
Expected: all green.

- [ ] **Step 12: Commit**

```bash
git add packages/mcp-server/src/folio_mcp/shell/ \
        packages/mcp-server/src/folio_mcp/core/__init__.py \
        packages/mcp-server/tests/folio_mcp/shell/ \
        packages/mcp-server/pyproject.toml
git commit -m "feat(mcp): add shell/ subpackage with tools and handler"
```

---

## Task 9: folio-mcp cleanup — remove old flat modules

**Files:**
- Delete: `packages/mcp-server/src/folio_mcp/config.py`
- Delete: `packages/mcp-server/src/folio_mcp/db.py`
- Delete: `packages/mcp-server/src/folio_mcp/tools/` (directory)
- Delete: `packages/mcp-server/src/folio_mcp/handler.py`
- Delete: `packages/mcp-server/tests/folio_mcp/test_search_docs.py`
- Delete: `packages/mcp-server/tests/folio_mcp/test_list_topics.py`
- Delete: `packages/mcp-server/tests/folio_mcp/test_get_document.py`
- Delete: `packages/mcp-server/tests/folio_mcp/test_mcp_handler.py`

- [ ] **Step 1: Delete old flat modules**

```bash
rm packages/mcp-server/src/folio_mcp/config.py \
   packages/mcp-server/src/folio_mcp/db.py \
   packages/mcp-server/src/folio_mcp/handler.py
rm -rf packages/mcp-server/src/folio_mcp/tools/
```

- [ ] **Step 2: Delete old flat tests**

```bash
rm packages/mcp-server/tests/folio_mcp/test_search_docs.py \
   packages/mcp-server/tests/folio_mcp/test_list_topics.py \
   packages/mcp-server/tests/folio_mcp/test_get_document.py \
   packages/mcp-server/tests/folio_mcp/test_mcp_handler.py
```

- [ ] **Step 3: Update conftest.py path** — `packages/mcp-server/tests/conftest.py` is shared across all mcp tests. No path changes needed — it only defines fixtures without imports from the package.

- [ ] **Step 4: Run tests — expect PASS**

```bash
uv run pytest packages/mcp-server/tests/ -m "not integration" -v
```
Expected: all green (only shell/ and core/ tests run).

- [ ] **Step 5: Commit**

```bash
git add -u packages/mcp-server/
git commit -m "refactor(mcp): remove old flat modules, keep only core/ and shell/"
```

---

## Task 10: folio-chat — new package

**Files:**
- Create: `packages/chat/pyproject.toml`
- Create: `packages/chat/src/folio_chat/__init__.py`
- Create: `packages/chat/src/folio_chat/core/__init__.py`
- Create: `packages/chat/src/folio_chat/shell/__init__.py`
- Create: `packages/chat/src/folio_chat/shell/app.py`
- Create: `packages/chat/src/folio_chat/shell/chat.py`
- Create: `packages/mcp-server/tests/folio_chat/__init__.py`
- Create: `packages/mcp-server/tests/folio_chat/test_chat_helpers.py`
- Modify: `pyproject.toml` (root workspace)
- Delete: `scripts/chat.py`, `scripts/web_chat.py`, `scripts/run_chainlit.py`

- [ ] **Step 1: Create package structure**

```bash
mkdir -p packages/chat/src/folio_chat/core \
          packages/chat/src/folio_chat/shell \
          packages/chat/tests/folio_chat
touch packages/chat/src/folio_chat/__init__.py \
      packages/chat/src/folio_chat/core/__init__.py \
      packages/chat/src/folio_chat/shell/__init__.py \
      packages/chat/tests/folio_chat/__init__.py
```

- [ ] **Step 2: Create pyproject.toml for folio-chat**

`packages/chat/pyproject.toml`:
```toml
[project]
name = "folio-chat"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "chainlit>=2.11.1",
    "fastmcp>=3.3.1",
    "litellm>=1.85.0",
    "mcp>=1.27.1",
    "ollama",
]

[tool.uv.sources]
folio-mcp = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 3: Add folio-chat to root workspace**

`pyproject.toml` root — add `"folio-chat"` to dependencies and the workspace member is auto-discovered via `packages/*`. Add to `[project] dependencies`:
```toml
dependencies = [
    "folio-core",
    "folio-mcp",
    "folio-sync",
    "folio-chat",
]
```

- [ ] **Step 4: Move scripts/web_chat.py → shell/app.py**

```bash
cp scripts/web_chat.py packages/chat/src/folio_chat/shell/app.py
```

No import changes needed — `web_chat.py` uses only stdlib and installed packages (chainlit, fastmcp, litellm). Verify no `scripts/` path references inside the file.

- [ ] **Step 5: Move scripts/chat.py → shell/chat.py**

```bash
cp scripts/chat.py packages/chat/src/folio_chat/shell/chat.py
```

- [ ] **Step 6: Update test_chat_helpers.py import path**

The current test at `packages/mcp-server/tests/folio_mcp/test_chat_helpers.py` loads `scripts/chat.py` via `importlib`. Move the test file and update the path:

```bash
mkdir -p packages/mcp-server/tests/folio_chat
touch packages/mcp-server/tests/folio_chat/__init__.py
```

`packages/mcp-server/tests/folio_chat/test_chat_helpers.py` — same content as original but update the path:
```python
"""Tests for chat helper functions."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import mcp.types

sys.modules.setdefault("ollama", MagicMock())

_spec = importlib.util.spec_from_file_location(
    "chat",
    Path(__file__).parents[4] / "packages" / "chat" / "src" / "folio_chat" / "shell" / "chat.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

mcp_tool_to_ollama = _mod.mcp_tool_to_ollama
extract_result_text = _mod.extract_result_text
DebugPrinter = _mod.DebugPrinter
OllamaAgent = _mod.OllamaAgent
```
(Keep existing test functions below — copy verbatim from original file.)

- [ ] **Step 7: Delete old test and scripts**

```bash
rm packages/mcp-server/tests/folio_mcp/test_chat_helpers.py \
   scripts/chat.py \
   scripts/web_chat.py \
   scripts/run_chainlit.py
```

- [ ] **Step 8: Install folio-chat into workspace**

```bash
uv sync
```

- [ ] **Step 9: Run tests — expect PASS**

```bash
uv run pytest packages/mcp-server/tests/folio_chat/ -v
```

- [ ] **Step 10: Commit**

```bash
git add packages/chat/ packages/mcp-server/tests/folio_chat/ pyproject.toml
git add -u scripts/
git commit -m "feat(chat): add folio-chat package, move scripts/web_chat.py and scripts/chat.py"
```

---

## Task 11: Lambda removal

**Files:**
- Delete: `Dockerfile.lambda`
- Delete: `scripts/build_lambdas.sh`
- Delete: `scripts/deploy_lambdas.sh`
- Delete: `scripts/deploy_mcp_lwa.sh`

- [ ] **Step 1: Delete Lambda artifacts**

```bash
rm Dockerfile.lambda \
   scripts/build_lambdas.sh \
   scripts/deploy_lambdas.sh \
   scripts/deploy_mcp_lwa.sh
```

- [ ] **Step 2: Run tests — expect PASS (nothing changed in code)**

```bash
uv run pytest -m "not integration" -v
```
Expected: all green.

- [ ] **Step 3: Commit**

```bash
git add -u
git commit -m "chore: remove Lambda artifacts (Dockerfile.lambda, build/deploy scripts)"
```

---

## Task 12: Per-package Dockerfiles + docker-compose services

**Files:**
- Create: `packages/doc-sync/Dockerfile`
- Create: `packages/mcp-server/Dockerfile`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Create packages/doc-sync/Dockerfile**

`packages/doc-sync/Dockerfile`:
```dockerfile
FROM python:3.14-rc-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN pip install uv

WORKDIR /app
COPY . /app

RUN uv sync --frozen --package folio-sync

CMD ["uv", "run", "folio-sync"]
```

- [ ] **Step 2: Create packages/mcp-server/Dockerfile**

`packages/mcp-server/Dockerfile`:
```dockerfile
FROM python:3.14-rc-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PORT=8001

RUN pip install uv

WORKDIR /app
COPY . /app

RUN uv sync --frozen --package folio-mcp

CMD ["uv", "run", "fastmcp", "run", \
     "packages/mcp-server/src/folio_mcp/shell/handler.py:mcp", \
     "--transport", "sse", "--host", "0.0.0.0", "--port", "8001"]
```

- [ ] **Step 3: Update docker-compose.yml**

`docker-compose.yml`:
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: folio
      POSTGRES_USER: folio
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U folio"]
      interval: 5s
      timeout: 3s
      retries: 5

  folio-sync:
    build:
      context: .
      dockerfile: packages/doc-sync/Dockerfile
    environment:
      FOLIO_SYNC_DATABASE__HOST: postgres
      FOLIO_SYNC_DATABASE__PORT: "5432"
      FOLIO_SYNC_DATABASE__NAME: folio
      FOLIO_SYNC_DATABASE__USER: folio
      FOLIO_SYNC_DATABASE__PASSWORD: dev
      FOLIO_SYNC_S3__ENDPOINT_URL: http://localstack:4566
      FOLIO_SYNC_S3__ACCESS_KEY: test
      FOLIO_SYNC_S3__SECRET_KEY: test
    depends_on:
      postgres:
        condition: service_healthy
    restart: "no"

  folio-mcp:
    build:
      context: .
      dockerfile: packages/mcp-server/Dockerfile
    environment:
      FOLIO_MCP_DATABASE__HOST: postgres
      FOLIO_MCP_DATABASE__PORT: "5432"
      FOLIO_MCP_DATABASE__NAME: folio
      FOLIO_MCP_DATABASE__USER: folio
      FOLIO_MCP_DATABASE__PASSWORD: dev
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  pgdata:
```

- [ ] **Step 4: Commit**

```bash
git add packages/doc-sync/Dockerfile packages/mcp-server/Dockerfile docker-compose.yml
git commit -m "feat(infra): add per-package Dockerfiles and docker-compose services"
```

---

## Task 13: infra/ directory reorganization

**Files:**
- Create: `infra/docker/localstack-init/01-bootstrap-aws.sh`
- Create: `infra/migrations/` (contents moved from `migrations/`)
- Create: `infra/seed/` (contents moved from `seed/`)
- Create: `infra/scripts/apply_migrations.py`
- Create: `infra/scripts/seed_localstack.py`
- Create: `infra/scripts/run_full_sync.py`
- Delete: original `docker/`, `migrations/`, `seed/`, and three infra scripts from `scripts/`
- Modify: `docker-compose.yml` (if volume mounts reference `docker/`)

- [ ] **Step 1: Move docker/, migrations/, seed/, and infra scripts**

```bash
mkdir -p infra/docker infra/scripts

# LocalStack init scripts
cp -r docker/localstack-init/ infra/docker/localstack-init/
rm -rf docker/

# Migrations
cp -r migrations/ infra/migrations/
rm -rf migrations/

# Seed
cp -r seed/ infra/seed/
rm -rf seed/

# Infrastructure scripts
cp scripts/apply_migrations.py infra/scripts/apply_migrations.py
cp scripts/seed_localstack.py infra/scripts/seed_localstack.py
cp scripts/run_full_sync.py infra/scripts/run_full_sync.py
rm scripts/apply_migrations.py scripts/seed_localstack.py scripts/run_full_sync.py
```

- [ ] **Step 2: Update scripts that reference seed/ or migrations/ paths**

Check `infra/scripts/apply_migrations.py` — if it references `migrations/` as a hard-coded path, update to `infra/migrations/`.

Check `infra/scripts/seed_localstack.py` — if it references `seed/` directory, update to `infra/seed/`.

- [ ] **Step 3: Update docker-compose.yml volume mounts if any reference `docker/`**

Check for `docker/` references:
```bash
grep -r "docker/" docker-compose.yml
```
If the LocalStack service mounts `docker/localstack-init/`, update to `infra/docker/localstack-init/`. Since LocalStack runs via `localstack start -d` (not via compose in current setup), this may not apply.

- [ ] **Step 4: Move chainlit.md**

```bash
mv chainlit.md packages/chat/chainlit.md
```

- [ ] **Step 5: Commit**

```bash
git add infra/ packages/chat/chainlit.md
git add -u docker/ migrations/ seed/ scripts/
git commit -m "refactor(infra): move docker, migrations, seed, scripts to infra/"
```

---

## Task 14: Makefile update

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Write new Makefile**

`Makefile`:
```makefile
.PHONY: up down clean ps logs migrate seed sync-full k8s-docs \
        serve serve-http chat chat-web \
        test lint typecheck format check bootstrap

NAME := folio

# === Infra ===
up:
	docker compose up -d
	@echo "Aguardando Postgres..."
	@until docker compose exec -T postgres pg_isready -U $(NAME) > /dev/null 2>&1; do sleep 1; done
	@echo "Iniciando LocalStack via CLI..."
	uv run localstack start -d
	@echo "Aguardando LocalStack..."
	uv run localstack wait -t 60
	@bash infra/docker/localstack-init/01-bootstrap-aws.sh
	$(MAKE) seed sync-full
	@echo "Stack pronta."

down:
	docker compose down
	uv run localstack stop

clean:
	docker compose down -v
	uv run localstack stop
	rm -rf dist/ _k8s-clone/

ps:
	docker compose ps
	uv run localstack status

logs:
	docker compose logs -f

# === Banco ===
migrate:
	uv run python infra/scripts/apply_migrations.py

# === Seed ===
k8s-docs:
	@echo "Clonando docs Kubernetes..."
	git clone --filter=blob:none --sparse \
	  https://github.com/kubernetes/website.git _k8s-clone
	cd _k8s-clone && git sparse-checkout set \
	  content/en/docs/concepts content/en/docs/tasks
	mkdir -p infra/seed/kubernetes-docs
	cp -r _k8s-clone/content/en/docs/concepts infra/seed/kubernetes-docs/
	cp -r _k8s-clone/content/en/docs/tasks infra/seed/kubernetes-docs/
	rm -rf _k8s-clone
	@echo "Docs: $$(find infra/seed/kubernetes-docs -name '*.md' | wc -l) arquivos"

seed:
	uv run python infra/scripts/seed_localstack.py
	@echo "S3: $$(uv run awslocal s3 ls s3://$(NAME)-docs --recursive | wc -l) objetos"

# === Sync ===
sync-full:
	uv run python infra/scripts/run_full_sync.py

# === Dev local ===
serve:
	uv run $(NAME)-mcp

serve-http:
	uv run fastmcp run packages/mcp-server/src/folio_mcp/shell/handler.py:mcp \
	  --transport sse --port 8001

chat:
	uv run packages/chat/src/folio_chat/shell/chat.py $(ARGS)

chat-web:
	@echo "Requer MCP server rodando: make serve-http (em outro terminal)"
	uv run chainlit run packages/chat/src/folio_chat/shell/app.py -w

start-localstack:
	uv run localstack start -d
	uv run localstack wait -t 60

# === Quality ===
test:
	uv run pytest -m "not integration" -v

coverage:
	uv run pytest -m "not integration" --cov --cov-report=term-missing

lint:
	uv run ruff check .

typecheck:
	uv run pyright packages/

format:
	uv run ruff format .

check: lint typecheck test
	@echo "Tudo verde."

# === Bootstrap completo ===
bootstrap: up migrate k8s-docs seed sync-full
	@echo ""
	@echo "Ambiente pronto."
	@echo "  Modo stdio   : make serve"
	@echo "  HTTP SSE     : make serve-http"
	@echo "  Chat CLI     : make chat"
	@echo "  Chat Web     : make chat-web"
	@echo "  Testes       : make check"
```

- [ ] **Step 2: Run tests via Makefile — expect PASS**

```bash
make test
```
Expected: all green.

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore(makefile): remove Lambda targets, update paths to infra/"
```

---

## Task 15: Documentation updates

**Files:**
- Modify: `AGENTS.md`
- Modify: `.agents/skills/python-fcis/SKILL.md`

- [ ] **Step 1: Update AGENTS.md — package table and FCIS section**

In `AGENTS.md`, replace the `## Packages` table:

```markdown
## Packages

| Package | Path | Role |
|---------|------|------|
| `folio-core` | `packages/core/` | Shared domain types and SQL helpers. Pure Python, no I/O. Only `models.py` and `sql.py`. |
| `folio-sync` | `packages/doc-sync/` | Event-driven S3→Postgres sync. Has own `core/` (parser, hasher, categorizer, indexer) and `shell/` (db, s3_client, indexer, handler). |
| `folio-mcp` | `packages/mcp-server/` | MCP server exposing `list_topics`, `search_docs`, `get_document`. Has own `core/` (queries, mappers) and `shell/` (db, tools, handler). |
| `folio-chat` | `packages/chat/` | Chainlit web UI and CLI REPL for local testing. |
```

Replace the `## Architecture: FCIS Layers` section:

```markdown
## Architecture: FCIS Layers

Each package (except `folio-core`) has explicit `core/` and `shell/` sub-packages:

- **`folio-core`** — shared minimum: `models.py` (domain types), `sql.py` (t-string helper). No sub-packages.
- **`package/core/`** — pure functions only. No DB, no HTTP, no filesystem. Testable without mocks.
- **`package/shell/`** — orchestrates I/O. Imports from own `core/` and `folio-core`. Calls core with concrete values, applies results to DB/S3/network.

**Import rules:**
- `*.core.*` may import from `folio_core` only.
- `*.shell.*` may import from `*.core.*` and `folio_core`.
- `folio_chat.*` may import from `folio_mcp` as a library client.
- `*.core.*` must **never** import from `*.shell.*`.
- `folio-core` must **never** import from any other workspace package.
```

Update the `## Dev Workflow` section to reference new paths:

```markdown
## Dev Workflow

```bash
make bootstrap      # full setup: infra + migrations + seed + sync
make up             # start Postgres + LocalStack, seed S3, sync to DB
make down           # stop all containers and LocalStack
make check          # lint + typecheck + tests (run before committing)
make test           # pytest only
make lint           # ruff check
make typecheck      # pyright on packages/
make serve          # run MCP server locally via stdio
make serve-http     # run MCP server via SSE on :8001
make chat           # CLI REPL (Ollama + MCP)
make chat-web       # Chainlit web UI (requires make serve-http)
```

Migrations: `infra/migrations/`. Apply with `make migrate`. Never alter schema directly.
Seed data: `infra/seed/`. Infrastructure scripts: `infra/scripts/`.
```

- [ ] **Step 2: Update python-fcis skill**

In `.agents/skills/python-fcis/SKILL.md` (and the referenced `references/module-structure.md`), update the module structure example to show `core/` and `shell/` subdirectories instead of flat layout. The key change: replace any flat-module example with:

```
folio_sync/
  core/
    __init__.py
    parser.py       # pure functions
    hasher.py       # pure functions
    categorizer.py  # pure functions
    indexer.py      # pure orchestration
  shell/
    __init__.py
    db.py           # I/O: psycopg pool
    s3_client.py    # I/O: boto3
    indexer.py      # I/O: DB writes, calls core/indexer.py
    handler.py      # entrypoint
```

- [ ] **Step 3: Run full test suite**

```bash
make check
```
Expected: lint + typecheck + tests all green.

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md .agents/skills/python-fcis/
git commit -m "docs: update AGENTS.md and python-fcis skill for new package structure"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|-----------------|------|
| folio-core shrinks to models.py + sql.py | Task 6 |
| folio-sync gets core/ with parser/hasher/categorizer | Task 2 |
| folio-sync/core/indexer.py (pure prepare_document) | Task 3 |
| folio-sync/shell/ with db, s3_client, config, indexer, handler | Task 4 |
| folio-mcp/core/ with queries.py, mappers.py | Task 7 |
| folio-mcp/shell/ with db, config, tools/, handler | Task 8 |
| folio-chat new package | Task 10 |
| Lambda removal (Dockerfile.lambda, scripts, handlers) | Task 11 |
| Per-package Dockerfiles | Task 12 |
| docker-compose folio-sync + folio-mcp services | Task 12 |
| infra/ directory reorganization | Task 13 |
| Makefile update | Task 14 |
| AGENTS.md + python-fcis skill update | Task 15 |
| chainlit.md move to packages/chat/ | Task 13 |
| pyproject.toml scripts entry point updates | Tasks 4, 8 |
| pyyaml moved from folio-core to folio-sync | Task 6 |

All spec requirements covered.

**Type consistency check:** `prepare_document` returns `dict` (Tasks 3, 4). `map_search_rows`/`map_topic_rows`/`map_document_row` parameter types consistent across Tasks 7 and 8. Query functions return `LiteralString`/`tuple[str,tuple]` consistent with usage in shell tools (Task 8).

**No placeholders found.**
