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
- `ty.toml`
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
