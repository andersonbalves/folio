# Python Setup Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `python-setup` skill that automates the configuration of Python repositories with strict standards for linting, type checking, security, and quality using separate configuration files.

**Architecture:** The skill uses static Jinja2-style templates stored in its own directory. A `SKILL.md` file contains the logic for "Smart-Default" detection and bilingual instructions.

**Tech Stack:** Python, Ruff, Ty (Pyright), Pytest, Pre-commit, Semgrep, Gitleaks, Qlty.

---

### Task 1: Create Directory Structure and Basic SKILL.md

**Files:**
- Create: `.agents/skills/python-setup/SKILL.md`
- Create: `.agents/skills/python-setup/templates/.gitkeep`

- [ ] **Step 1: Create the directory structure**
Run: `mkdir -p .agents/skills/python-setup/templates`

- [ ] **Step 2: Create initial SKILL.md with metadata**
```markdown
---
name: python-setup
description: Use when setting up or auditing a Python repository configuration for linting, type checking, security, and quality (Ruff, Ty, Pytest, Pre-commit, Qlty, etc.). / Use para configurar ou auditar repositórios Python com padrões rigorosos de linting, tipagem, segurança e qualidade.
---

# Python Setup

## Overview / Visão Geral
Automates "Strict & Secure" repository configuration. / Automatiza a configuração "Strict & Secure" do repositório.

## When to Use / Quando Usar
- New Python project or package. / Novo projeto ou pacote Python.
- Migrating config from `pyproject.toml` to separate files. / Migrando config do `pyproject.toml` para arquivos separados.
- Adding security tools (Gitleaks, Semgrep). / Adicionando ferramentas de segurança.
- Standardizing quality metrics (Qlty). / Padronizando métricas de qualidade.

[Rest of content will be added in later tasks]
```

- [ ] **Step 3: Commit**
```bash
git add .agents/skills/python-setup/
git commit -m "feat(skills): initialize python-setup skill structure"
```

### Task 2: Implement Ruff Template

**Files:**
- Create: `.agents/skills/python-setup/templates/ruff.toml.j2`

- [ ] **Step 1: Create the Ruff template**
```toml
# Ruff configuration - Strict & Secure
# https://docs.astral.sh/ruff/settings/

line-length = {{ line_length | default(100) }}
target-version = "{{ target_version | default('py312') }}"

[lint]
# E: pycodestyle errors, F: Pyflakes, I: isort, N: pep8-naming, W: pycodestyle warnings
# UP: pyupgrade, B: flake8-bugbear, SIM: flake8-simplify, RET: flake8-return
# PTH: flake8-use-pathlib, T20: flake8-print
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "RET", "PTH", "T20"]
ignore = []

[lint.isort]
known-first-party = ["{{ project_name }}"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

- [ ] **Step 2: Commit**
```bash
git add .agents/skills/python-setup/templates/ruff.toml.j2
git commit -m "feat(skills): add ruff template to python-setup"
```

### Task 3: Implement Ty (Pyright) Template

**Files:**
- Create: `.agents/skills/python-setup/templates/pyrightconfig.json.j2`

- [ ] **Step 1: Create the Pyright template**
```json
{
  "include": ["{{ src_dir | default('src') }}", "packages/*/src"],
  "exclude": ["**/node_modules", "**/__pycache__", ".venv"],
  "typeCheckingMode": "strict",
  "reportMissingImports": true,
  "reportUnusedVariable": true,
  "reportUnusedImport": true,
  "pythonVersion": "{{ python_version | default('3.12') }}",
  "executionEnvironments": [
    {
      "root": "."
    }
  ]
}
```

- [ ] **Step 2: Commit**
```bash
git add .agents/skills/python-setup/templates/pyrightconfig.json.j2
git commit -m "feat(skills): add pyrightconfig template to python-setup"
```

### Task 4: Implement Pytest and Qlty Templates

**Files:**
- Create: `.agents/skills/python-setup/templates/pytest.ini.j2`
- Create: `.agents/skills/python-setup/templates/.qlty.toml.j2`

- [ ] **Step 1: Create the Pytest template**
```ini
[pytest]
asyncio_mode = auto
testpaths = {{ test_paths | default('tests') }}
python_files = test_*.py
python_functions = test_*
filterwarnings =
    error
```

- [ ] **Step 2: Create the Qlty template**
```toml
# Qlty configuration
# https://qlty.sh/docs/configuration

[metrics]
complexity = { threshold = 10 }
duplication = { threshold = 5 }

[python]
version = "{{ python_version | default('3.12') }}"

[coverage]
enabled = true
threshold = 80
```

- [ ] **Step 3: Commit**
```bash
git add .agents/skills/python-setup/templates/pytest.ini.j2 .agents/skills/python-setup/templates/.qlty.toml.j2
git commit -m "feat(skills): add pytest and qlty templates to python-setup"
```

### Task 5: Implement Pre-commit and Security Templates

**Files:**
- Create: `.agents/skills/python-setup/templates/.pre-commit-config.yaml.j2`
- Create: `.agents/skills/python-setup/templates/.semgrep.yml.j2`
- Create: `.agents/skills/python-setup/templates/.gitleaks.toml.j2`

- [ ] **Step 1: Create the Pre-commit template**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: ty
        name: ty
        entry: uv run ty
        language: system
        types: [python]
        pass_filenames: false

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.2
    hooks:
      - id: gitleaks

  - repo: https://github.com/returntocorp/semgrep
    rev: v1.72.0
    hooks:
      - id: semgrep
        args: ['--config', 'auto', '--error']
```

- [ ] **Step 2: Create the Semgrep template (placeholder for custom rules)**
```yaml
rules:
  - id: custom-python-rule
    patterns:
      - pattern: print(...)
    message: "Use logging instead of print()"
    languages: [python]
    severity: WARNING
```

- [ ] **Step 3: Create the Gitleaks template**
```toml
[allowlist]
description = "Global allowlist"
paths = [
    "pyproject.toml",
    "uv.lock"
]
```

- [ ] **Step 4: Commit**
```bash
git add .agents/skills/python-setup/templates/.pre-commit-config.yaml.j2 .agents/skills/python-setup/templates/.semgrep.yml.j2 .agents/skills/python-setup/templates/.gitleaks.toml.j2
git commit -m "feat(skills): add pre-commit and security templates to python-setup"
```

### Task 6: Finalize SKILL.md with Bilingual Instructions and Logic

**Files:**
- Modify: `.agents/skills/python-setup/SKILL.md`

- [ ] **Step 1: Complete SKILL.md content**
```markdown
[... previous content ...]

## Logic: Smart-Default Detection / Lógica: Detecção Smart-Default

1. **Workspace Check:** Look for `[tool.uv.workspace]` in root `pyproject.toml`.
2. **Context Selection:**
   - If Workspace: Ask if config is for **Root** (shared) or **Package** (`packages/X`).
   - If Standalone: Use **Root**.
3. **Migration:**
   - Read existing `[tool.ruff]`, `[tool.pytest.ini_options]`, etc., from `pyproject.toml`.
   - Map values to templates.
   - Delete these sections from `pyproject.toml`.

## Execution Steps / Passos de Execução

### 1. Detection / Detecção
Identify project structure and existing configs. / Identificar estrutura e configs existentes.

### 2. File Creation / Criação de Arquivos
Create files from templates, replacing placeholders: / Criar arquivos a partir dos templates, substituindo os placeholders:
- `ruff.toml`
- `pyrightconfig.json` (for Ty)
- `pytest.ini`
- `.pre-commit-config.yaml`
- `.qlty.toml`
- `.semgrep.yml`
- `.gitleaks.toml`

### 3. Dependency Check / Dependências
Ensure tools are in `pyproject.toml` (dev dependencies): / Garantir ferramentas no `pyproject.toml`:
`uv add --dev ruff ty pytest pre-commit`

### 4. Activation / Ativação
Run: `pre-commit install`

## Success Criteria / Critérios de Sucesso
- `uv run ruff check` passes.
- `uv run ty` passes.
- `uv run pytest` passes.
- `pre-commit run --all-files` passes.
```

- [ ] **Step 2: Commit**
```bash
git add .agents/skills/python-setup/SKILL.md
git commit -m "feat(skills): finalize python-setup SKILL.md"
```
