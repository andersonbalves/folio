# Agent Config Files Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` at the project root to orient AI coding assistants to Folio's architecture, workflow, and conventions.

**Architecture:** `AGENTS.md` is the canonical source of truth (~70 lines, English). `CLAUDE.md` uses `@AGENTS.md` include and adds a Claude Code–specific addendum listing available skills. `GEMINI.md` is a symlink to `AGENTS.md`.

**Tech Stack:** Markdown, `ln -s` for symlink. No code, no tests — these are documentation files.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `AGENTS.md` | Create | Shared content: overview, packages, stack, dev workflow, FCIS rules, conventions |
| `CLAUDE.md` | Create | `@AGENTS.md` include + Claude Code addendum (skills list) |
| `GEMINI.md` | Create (symlink) | `ln -s AGENTS.md GEMINI.md` |

---

### Task 1: Create AGENTS.md

**Files:**
- Create: `AGENTS.md`

- [ ] **Step 1: Create the file with full content**

Create `/home/baratella/w/folio/folio/AGENTS.md` with this exact content:

```markdown
# Folio

Knowledge management system (RAG-ready): syncs Markdown documents from S3 to Postgres
with full-text/vector search, exposing search tools via the Model Context Protocol (MCP).

## Packages

| Package | Path | Role |
|---------|------|------|
| `folio-core` | `packages/core/` | Domain logic: parsing, hashing, categorization. Pure Python, no I/O. |
| `folio-sync` | `packages/doc-sync/` | Event-driven S3→Postgres sync via SQS/SNS. Lambda handler + indexer. |
| `folio-mcp` | `packages/mcp-server/` | MCP server exposing `list_topics`, `search_docs`, `get_document` tools. |

## Stack

- Python 3.14+, `uv` workspace monorepo (`pyproject.toml` at root + per package)
- Postgres with pgvector and BM25 full-text search
- LocalStack for local AWS emulation (S3, SQS, Lambda, SNS)
- Chainlit for conversational web UI
- MCP protocol (via `fastmcp`) for tool exposure to AI assistants

## Dev Workflow

```bash
make bootstrap      # full setup: infra + migrations + seed + lambda deploy
make up             # start Postgres + LocalStack, seed S3, sync to DB
make down           # stop all containers and LocalStack
make check          # lint + typecheck + tests (run before committing)
make test           # pytest only
make lint           # ruff check
make typecheck      # pyright on packages/
make serve          # run MCP server locally via stdio
make chat-web       # Chainlit web UI (connects to LocalStack-hosted MCP)
make deploy-mcp     # build + deploy MCP Lambda to LocalStack
```

## Architecture: FCIS Layers

Each package follows Functional Core / Imperative Shell. Modules are flat (no subdirs),
but responsibilities are separated by convention:

- **Core** (`folio-core`): pure functions only. `parser.py`, `hasher.py`, `categorizer.py`,
  `models.py`. No DB, no HTTP, no filesystem. Business logic and data transformations.
- **Shell** (`folio-sync`, `folio-mcp`): orchestrates I/O. `db.py` (Postgres), `s3_client.py`
  (S3), `handler.py` (entrypoint). Calls core with concrete values, applies results.

**Import rule:** shell modules import core; core never imports shell. `folio-sync` and
`folio-mcp` depend on `folio-core`; `folio-core` has no workspace dependencies.

## Conventions

- **Dependencies:** always `uv add` / `uv run`. Never `pip` directly.
- **Tests:** core modules → unit tests, no mocks. Shell modules → integration tests,
  mock only system boundaries (DB driver, boto3 client). See `python-testing` skill.
- **Code quality:** `ruff` for formatting and linting, `pyright` for type checking.
  Run `make check` before every commit.
- **Migrations:** SQL files in `migrations/`. Apply with `make migrate`. Never alter
  the schema directly on the DB.

## Out of Scope

- Do not use `pip`, `poetry`, or `conda` — `uv` only.
- Do not import from `folio-sync` or `folio-mcp` inside `folio-core`.
- Do not mock functions you wrote inside `folio-sync` or `folio-mcp` — only mock
  the outermost system boundary (e.g. `boto3.client`, psycopg connection factory).
```

- [ ] **Step 2: Verify file looks right**

```bash
wc -l AGENTS.md
cat AGENTS.md
```

Expected: ~75 lines, no trailing whitespace issues.

- [ ] **Step 3: Stage and verify pre-commit passes**

```bash
git add AGENTS.md
git stash  # don't commit yet — do all three files together
git stash pop
```

Actually just leave staged for now — commit in Task 4.

---

### Task 2: Create CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create the file**

Create `/home/baratella/w/folio/folio/CLAUDE.md` with this exact content:

```markdown
@AGENTS.md

## Claude Code

Skills in `.agents/skills/` (symlinked to `.claude/skills/`) — invoke via the Skill tool
before implementing features or writing tests:

- `python-fcis` — FCIS architecture guide and patterns
- `python-testing` — test strategy per layer, naming, mock policy
- `python-dependency-management` — uv workspace rules, adding packages
- `python-mutation-testing` — mutation testing with mutmut
- `python-setup` — environment setup steps
- `git-workflow` — branch naming, commit conventions, PR workflow
```

- [ ] **Step 2: Verify**

```bash
cat CLAUDE.md
```

Expected: `@AGENTS.md` on line 1, then blank line, then `## Claude Code` section.

---

### Task 3: Create GEMINI.md symlink

**Files:**
- Create: `GEMINI.md` (symlink → `AGENTS.md`)

- [ ] **Step 1: Create symlink**

```bash
ln -s AGENTS.md GEMINI.md
```

- [ ] **Step 2: Verify symlink resolves correctly**

```bash
ls -la GEMINI.md
cat GEMINI.md | head -5
```

Expected:
```
GEMINI.md -> AGENTS.md
# Folio
...
```

---

### Task 4: Commit all three files

- [ ] **Step 1: Stage all three**

```bash
git add AGENTS.md CLAUDE.md GEMINI.md
git status
```

Expected: 3 new files staged.

- [ ] **Step 2: Commit**

```bash
git commit -m "docs: add AGENTS.md, CLAUDE.md, GEMINI.md for AI assistant orientation"
```

- [ ] **Step 3: Verify commit**

```bash
git log --oneline -3
git show --stat HEAD
```

Expected: latest commit shows 3 files, `GEMINI.md` listed as symlink.
