---
name: phase9-dx-design
description: Design for Phase 9 — DX finalization: Makefile alignment and full README walkthrough
metadata:
  type: project
---

# Phase 9 — Finalização e DX

**Date:** 2026-05-16
**Status:** approved
**Approach:** B — Full spec alignment

---

## Context

All functional phases (0–8) are complete:
- 25 tests passing, lint and typecheck clean
- Both Lambda ZIPs built (`dist/folio-sync.zip`, `dist/folio-mcp.zip`)
- Kubernetes docs seed present (`seed/kubernetes-docs/`)
- Makefile and README exist but need gaps fixed

Phase 9 delivers DX polish: a complete, verified Makefile and a README that allows a new developer to be running in < 10 minutes.

---

## Makefile Changes

Two targeted fixes only. Everything else is working and stays untouched.

### 1. Add `worker` target

`worker` is declared in `.PHONY` but has no recipe — `make worker` would fail with "No rule to make target". The worker runs the doc-sync Lambda logic locally in polling mode (CLI entry point).

```makefile
worker:
	uv run folio-sync
```

### 2. Switch `typecheck` to `ty`

Current: `uv run pyright packages/`
Target: `uv run ty check packages/`

Reason: `ty.toml` is present, git history shows intentional migration (`fix(skills): use ty.toml instead of pyrightconfig.json for ty`), and PROMPT.md spec says `ty`. `ty check` already passes clean.

---

## README Structure

Full walkthrough, targeting < 10 min for a new dev. Sections:

### 1. What is Folio
Two sentences: BM25 lexical search over internal Markdown docs, exposed via MCP (Model Context Protocol). No vector DB — lexical filter + LLM reader.

### 2. Architecture
Keep current 3-bullet summary (core/sync/mcp packages).

### 3. Prerequisites
- Python 3.14+
- uv (`pip install uv` or `brew install uv`)
- Docker + Docker Compose
- LocalStack CLI (`pip install localstack`)
- `awslocal` — auto-installed as LocalStack dependency

### 4. Quick Start
Single command: `make bootstrap`. Explanation of what it does (up → migrate → k8s-docs → seed → sync-full → build → deploy-local).

### 5. Step-by-Step Setup
Numbered walkthrough for those who want control over each phase. Includes expected output at each step.

### 6. Testing with MCP Inspector
```bash
npx @modelcontextprotocol/inspector uv run folio-mcp
```
Expected: browser opens at localhost:5173, shows three tools: `list_topics`, `search_docs`, `get_document`.

### 7. Connecting Claude Desktop
JSON config snippet in `claude_desktop_config.json`. Include table of env vars for database/S3 overrides.

### 8. Make Targets Reference
Table: target → what it does → when to use.

### 9. Known Limitations
- **Lexical-only search:** BM25 via Postgres `tsvector`. Semantic/embedding search not implemented.
- **No authentication:** MCP server has no auth. Stdio mode only in production use.
- **LocalStack only:** No real AWS deploy scripts. Lambda build artifacts work with real AWS but deploy scripts target LocalStack.
- **Python 3.14 required:** Uses PEP 750 t-strings — no fallback for 3.12/3.13.
- **Stdio blocks Claude Desktop:** Each tool call spawns the full server — cold start latency ~1-2s.
- **No observability:** structlog to stderr only. No CloudWatch/Firehose pipeline (planned for next iteration).

---

## Success Criteria

- [ ] `make check` passes (lint + typecheck + tests)
- [ ] `make worker` no longer fails
- [ ] `typecheck` runs `ty check`, not `pyright`
- [ ] README has all 9 sections
- [ ] New dev can follow README to running server in < 10 min
