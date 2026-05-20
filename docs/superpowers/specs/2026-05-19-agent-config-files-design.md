# Design: AGENTS.md / CLAUDE.md / GEMINI.md

**Date:** 2026-05-19
**Status:** Approved

## Goal

Create AI assistant instruction files at the project root so any AI coding tool (Claude Code, Gemini CLI, Codex, etc.) gets oriented to Folio's architecture, dev workflow, and coding conventions without duplicating what the existing `.agents/skills/` already cover in detail.

## Files

| File | Strategy |
|------|----------|
| `AGENTS.md` | Canonical shared content (~70 lines). Architecture, dev commands, layer rules, conventions. |
| `CLAUDE.md` | `@AGENTS.md` include + Claude-specific addendum listing available skills. |
| `GEMINI.md` | Symlink to `AGENTS.md`. |

## AGENTS.md Content

### Sections

1. **Project overview** — 2-3 sentences describing Folio (RAG-ready KMS, S3→Postgres sync, MCP tools).
2. **Packages table** — `folio-core`, `folio-sync`, `folio-mcp` with one-line role each.
3. **Stack** — Python 3.14+, uv workspace, Postgres/pgvector, LocalStack, Chainlit, MCP.
4. **Dev workflow** — ~8 key `make` targets with one-line descriptions.
5. **FCIS layers** — brief summary: domain (pure), infra (I/O), app (wiring). Import rule. Points to `python-fcis` skill for detail.
6. **Conventions** — 4 bullets: uv-only deps, test strategy per layer, ruff/pyright for quality, SQL migrations.
7. **Out of scope** — 3 hard nots: no pip, no reverse imports, no internal mocks.

### Key constraints

- **Language:** English.
- **Length:** ~70 lines — orient, don't document. Skills handle depth.
- **No duplication:** FCIS rules are a summary; `python-fcis` and `python-testing` skills are authoritative.

## CLAUDE.md Content

```
@AGENTS.md

## Claude Code

Skills in `.agents/skills/` (symlinked to `.claude/skills/`) — invoke via Skill tool before implementing:

- `python-fcis` — FCIS architecture guide
- `python-testing` — test strategy per layer
- `python-dependency-management` — uv workspace rules
- `python-mutation-testing` — mutation testing with mutmut
- `git-workflow` — branch/commit/PR workflow
```

## GEMINI.md

Symlink: `GEMINI.md -> AGENTS.md`

Gemini CLI reads `GEMINI.md` from project root. No Gemini-specific addendum needed (no equivalent skills system).

## Non-goals

- Documenting every make target (README covers this).
- Replacing or extending skill content.
- Adding RTK rules (already in `.agents/rules/antigravity-rtk-rules.md` and user's global CLAUDE.md).
