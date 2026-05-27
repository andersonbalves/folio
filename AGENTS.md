# Folio

Knowledge management system (RAG-ready): indexes local Markdown documents into a SQLite database with full-text search (BM25 via FTS5), exposing search tools via the Model Context Protocol (MCP). The whole project is distributed as a standalone Docker image.

## Packages

| Package | Path | Role |
|---------|------|------|
| `folio-core` | `packages/core/` | Shared domain types and SQL helpers. Pure Python, no I/O. Only `models.py` and `sql.py`. |
| `folio-sync` | `packages/doc-sync/` | Local directory indexer. Has own `core/` (parser, hasher, categorizer, indexer) and `shell/` (db, cli). Reads from local `data/` and upserts to SQLite. |
| `folio-mcp` | `packages/mcp-server/` | MCP server exposing `list_topics`, `search_docs`, `get_document`. Has own `core/` (queries, mappers) and `shell/` (db, tools, handler) running synchronous SQLite queries. |
| `folio-chat` | `packages/chat/` | Chainlit web UI and CLI REPL for local testing. |

## Stack

- Python 3.14+, `uv` workspace monorepo (`pyproject.toml` at root + per package)
- SQLite with `sqlite-vec` extension and FTS5 full-text search
- Docker (multi-stage builds for the standalone image)
- Chainlit for conversational web UI
- MCP protocol (via `fastmcp`) for tool exposure to AI assistants

## Dev Workflow

```bash
make k8s-docs       # clone Kubernetes documentation into data/ for testing
make index          # parse data/ and build folio.sqlite database
make build-image    # build the standalone Docker image (folio-mcp)
make check          # lint + typecheck + tests (run before committing)
make test           # pytest only
make lint           # ruff check
make typecheck      # pyright on packages/
make serve          # run MCP server locally via stdio
make serve-http     # run MCP server via SSE on :8001
make chat           # CLI REPL (Ollama + MCP)
make chat-web       # Chainlit web UI (requires make serve-http)
```

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
