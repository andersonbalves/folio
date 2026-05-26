---
name: python-dependency-management
description: >
  Use ao adicionar, atualizar ou gerenciar dependências Python com uv, ao trabalhar com
  workspaces UV (monorepos), dependências locais entre pacotes, ou ao refatorar projetos
  para estrutura de workspace. Aplique sempre que o usuário mencionar uv, pyproject.toml,
  uv add, uv sync, workspace, ou tiver dúvidas sobre onde adicionar uma dependência
  num monorepo Python. /
  Use when adding, updating, or managing Python dependencies with uv, or when working with
  UV workspaces (monorepos), local package dependencies, or refactoring projects to workspace
  structures. Apply whenever the user mentions uv, pyproject.toml, uv add, uv sync, workspace,
  or has questions about where to add a dependency in a Python monorepo.
---

# Python Dependency Management with uv

## Overview
Always use the `uv` CLI to manage dependencies. `uv` provides a unified interface for both single-package projects and multi-package workspaces (monorepos), ensuring lockfile consistency and resolution safety.

## The Rule
**NEVER manually edit `pyproject.toml` or `requirements.txt` to add or update packages.** You must use `uv add <package>` (or `uv add --package <name> <package>` in workspaces). This ensures the resolver runs correctly, the lockfile (`uv.lock`) is updated, and compatible versions are used.

## Red Flags - STOP and Start Over
If you catch yourself doing any of the following, STOP and use `uv` commands instead:
- "I'll just quickly add this line to `pyproject.toml`."
- "I already know the latest version number."
- Running `pip install` directly.
- Running `uv sync` inside a workspace member directory (always run from root).

## UV Workspaces (Monorepos)
A workspace is a collection of Python packages sharing a single `.venv` and a single `uv.lock`.

### Structure
```
my-project/
├── pyproject.toml      ← workspace root (defines members)
├── uv.lock             ← unified lockfile
├── packages/
│   ├── core/           ← member package
│   │   └── pyproject.toml
│   └── api/            ← member package
│       └── pyproject.toml
```

### Configuration
Root `pyproject.toml` (virtual workspace):
```toml
[tool.uv.workspace]
members = ["packages/*"]
```

Member `pyproject.toml` referencing another local package:
```toml
[project]
name = "api"
dependencies = ["core"]

[tool.uv.sources]
core = { workspace = true }
```

## Essential Commands
| Action | Single Package | Workspace (Run from Root) |
|--------|----------------|---------------------------|
| Add package | `uv add <pkg>` | `uv add --package <member> <pkg>` |
| Add dev package | `uv add --dev <pkg>` | `uv add --package <member> --dev <pkg>` |
| Remove package | `uv remove <pkg>` | `uv remove --package <member> <pkg>` |
| Sync environment | `uv sync` | `uv sync` |
| Run command | `uv run <cmd>` | `uv run --package <member> <cmd>` |

## Common Pitfalls
- **Local .venv in members:** UV may create a local `.venv` if run inside a member folder. Delete it; workspaces use only the root `.venv`.
- **Build-system missing:** Every member package MUST have a `[build-system]` section (e.g., using `hatchling`).
- **Path Hacks:** Never use `sys.path` to import local packages; use `{ workspace = true }` in `[tool.uv.sources]`.
