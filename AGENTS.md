# Folio

Knowledge management system (RAG-ready): syncs Markdown documents from S3 to Postgres
with full-text/vector search, exposing search tools via the Model Context Protocol (MCP).

## Packages

| Package | Path | Role |
|---------|------|------|
| `folio-core` | `packages/core/` | Shared domain types and SQL helpers. Pure Python, no I/O. Only `models.py` and `sql.py`. |
| `folio-sync` | `packages/doc-sync/` | Event-driven S3→Postgres sync. Has own `core/` (parser, hasher, categorizer, indexer) and `shell/` (db, s3_client, indexer, handler). |
| `folio-mcp` | `packages/mcp-server/` | MCP server exposing `list_topics`, `search_docs`, `get_document`. Has own `core/` (queries, mappers) and `shell/` (db, tools, handler). |
| `folio-chat` | `packages/chat/` | Chainlit web UI and CLI REPL for local testing. |

## Stack

- Python 3.14+, `uv` workspace monorepo (`pyproject.toml` at root + per package)
- Postgres with pgvector and BM25 full-text search
- LocalStack for local AWS emulation (S3, SQS, SNS)
- Chainlit for conversational web UI
- MCP protocol (via `fastmcp`) for tool exposure to AI assistants

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

## Conventions

- **Dependencies:** always `uv add` / `uv run`. Never `pip` directly.
- **Tests:** core modules → unit tests, no mocks. Shell modules → integration tests,
  mock only system boundaries (DB driver, boto3 client). See `python-testing` skill.
- **Code quality:** `ruff` for formatting and linting, `pyright` for type checking.
  Run `make check` before every commit.

## Out of Scope

- Do not use `pip`, `poetry`, or `conda` — `uv` only.
- Do not import from `folio-sync` or `folio-mcp` inside `folio-core`.
- Do not mock functions you wrote inside `folio-sync` or `folio-mcp` — only mock
  the outermost system boundary (e.g. `boto3.client`, psycopg connection factory).
