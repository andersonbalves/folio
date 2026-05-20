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
