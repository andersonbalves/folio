# Design Spec: Python Setup Skill (python-setup)

**Date:** 2026-05-15
**Status:** Draft

## 1. Overview
The `python-setup` skill is a tool for automating the configuration of Python repositories with high standards for linting, type checking, security, and code quality. It prioritizes separate configuration files over a monolithic `pyproject.toml` and uses static templates with minimal placeholders.

### Goals
- Automate repository setup with a "Strict & Secure" baseline.
- Support "Smart-Default" detection for Monorepo (uv workspaces) vs. Single Package.
- Provide bilingual (PT-BR/EN) instructions and documentation.
- Implement security and quality tools: Ruff, Ty (Pyright), Pytest, Pre-commit, Gitleaks, Semgrep, and Qlty.

## 2. Architecture & Components

### Skill Directory Structure
```
.agents/skills/python-setup/
├── SKILL.md                 # Bilingual instructions and logic
├── templates/
│   ├── ruff.toml.j2         # Ruff config (Lint & Format)
│   ├── pyrightconfig.json.j2 # Ty/Pyright config (Strict mode)
│   ├── pytest.ini.j2        # Pytest config (Async auto, warnings as errors)
│   ├── .pre-commit-config.yaml.j2 # Pre-commit hooks (including security)
│   ├── .qlty.toml.j2        # Comprehensive Qlty config
│   ├── .semgrep.yml.j2      # Custom security rules (if needed)
│   └── .gitleaks.toml.j2    # Custom secret patterns
```

### Tooling Strategy
- **Linting & Formatting:** Ruff (strict ruleset).
- **Type Checking:** Ty (wrapper for Pyright) in `strict` mode.
- **Testing:** Pytest with `asyncio` and error-on-warnings.
- **Security:** Gitleaks (secrets) and Semgrep (SAST) integrated via Pre-commit hooks.
- **Quality:** Qlty with cyclomatic complexity and coverage metrics.

## 3. "Smart-Default" Logic
The skill will follow this decision tree:
1. **Detect Project Type:**
   - If `[tool.uv.workspace]` exists in root `pyproject.toml` -> **Workspace Mode**.
   - Otherwise -> **Standalone Mode**.
2. **Determine Target Directory:**
   - If Workspace: Ask user if config is root-wide or for a specific package in `packages/*`.
   - If Standalone: Use root.
3. **Migrate existing config:**
   - Detect `[tool.ruff]`, `[tool.pytest]`, etc., in `pyproject.toml`.
   - Extract values to fill templates.
   - Remove these sections from `pyproject.toml`.

## 4. Configuration Rules (The "Strict" Baseline)

### Ruff (`ruff.toml`)
- Select: `E`, `F`, `I`, `N`, `W`, `UP`, `B`, `SIM`, `RET`, `PTH`, `T20` (prohibit print).
- Line length: 100.
- Target version: py312 (default, configurable).

### Ty (`pyrightconfig.json`)
- `typeCheckingMode`: "strict".
- `reportMissingImports`: true.
- `reportUnusedVariable`: true.

### Pytest (`pytest.ini`)
- `asyncio_mode = "auto"`.
- `filterwarnings = "error"`.

### Qlty (`.qlty.toml`)
- Comprehensive setup including:
  - Complexity thresholds.
  - Duplication detection.
  - Coverage requirements (if applicable).
  - Language-specific rules for Python.

### Pre-commit (`.pre-commit-config.yaml`)
- Hooks: `ruff-format`, `ruff-check`, `ty`, `gitleaks`, `semgrep`.

## 5. Bilingual Support
- `SKILL.md` will contain sections for both Portuguese and English.
- Tool descriptions and commit message suggestions will be provided in both languages.

## 6. Implementation Plan
1. Create directory structure.
2. Define static templates with Jinja2-style placeholders.
3. Write `SKILL.md` with detection logic and bilingual instructions.
4. Add verification steps (installing pre-commit, running ty).
