# Update Python requirement to 3.14 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update project Python version requirement to 3.14 across all configuration files and documentation.

**Architecture:** Surgical update of `pyproject.toml` files, `.python-version`, and documentation. Sync workspace using `uv`.

**Tech Stack:** Python 3.14, uv, ruff.

---

### Task 1: Update Root Configuration

**Files:**
- Modify: `pyproject.toml`
- Modify: `.python-version`

- [ ] **Step 1: Update `pyproject.toml` (root)**
Update `requires-python` and `target-version`.
```toml
requires-python = ">=3.14"
[tool.ruff]
target-version = "py314"
```

- [ ] **Step 2: Update `.python-version`**
```text
3.14
```

- [ ] **Step 3: Commit**
```bash
git add pyproject.toml .python-version
git commit -m "chore: update root python requirement to 3.14"
```

### Task 2: Update Package Configuration

**Files:**
- Modify: `packages/core/pyproject.toml`
- Modify: `packages/doc-sync/pyproject.toml`
- Modify: `packages/mcp-server/pyproject.toml`

- [ ] **Step 1: Update `packages/core/pyproject.toml`**
```toml
requires-python = ">=3.14"
```

- [ ] **Step 2: Update `packages/doc-sync/pyproject.toml`**
```toml
requires-python = ">=3.14"
```

- [ ] **Step 3: Update `packages/mcp-server/pyproject.toml`**
```toml
requires-python = ">=3.14"
```

- [ ] **Step 4: Commit**
```bash
git add packages/core/pyproject.toml packages/doc-sync/pyproject.toml packages/mcp-server/pyproject.toml
git commit -m "chore: update package python requirement to 3.14"
```

### Task 3: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `PROMPT.md`

- [ ] **Step 1: Update `README.md`**
Change `Python 3.12+` to `Python 3.14`.

- [ ] **Step 2: Update `PROMPT.md`**
Update all Python 3.12 references to 3.14.

- [ ] **Step 3: Commit**
```bash
git add README.md PROMPT.md
git commit -m "docs: update python requirement to 3.14"
```

### Task 4: Sync Workspace

- [ ] **Step 1: Run `uv sync`**
```bash
uv sync
```

- [ ] **Step 2: Verify `uv.lock`**
Ensure `python = ">=3.14"` is present.

- [ ] **Step 3: Commit**
```bash
git add uv.lock
git commit -m "chore: sync workspace for python 3.14"
```
