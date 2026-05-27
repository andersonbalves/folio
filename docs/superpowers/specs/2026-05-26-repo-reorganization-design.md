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
