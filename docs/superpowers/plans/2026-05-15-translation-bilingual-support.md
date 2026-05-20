# Translation and Bilingual Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Translate internal codebase to English and implement bilingual (EN/PT-BR) support for the MCP server using a facade pattern.

**Architecture:** Use a "Facade" pattern in `handler.py` for MCP tools to centralize bilingual metadata while keeping logic in separate modules. Translate all docstrings and comments in the core and sync packages to English.

**Tech Stack:** Python 3.12, FastMCP, Pytest.

---

### Task 1: Translate Core Package

**Files:**
- Modify: `packages/core/src/folio_core/categorizer.py`
- Modify: `packages/core/src/folio_core/hasher.py`
- Modify: `packages/core/src/folio_core/parser.py`
- Modify: `packages/core/src/folio_core/models.py`

- [ ] **Step 1: Translate `categorizer.py` docstrings and comments**
  Change module docstring and function descriptions to English.
- [ ] **Step 2: Translate `hasher.py` docstrings and comments**
  Change module docstring and `sha256_hash` description to English.
- [ ] **Step 3: Translate `parser.py` docstrings and comments**
  Change docstrings for `parse_markdown` and other helpers.
- [ ] **Step 4: Translate `models.py` docstrings**
  Translate pydantic model docstrings.
- [ ] **Step 5: Run tests to ensure no regressions**
  Run: `uv run pytest packages/core/tests/`
- [ ] **Step 6: Commit**
  Run: `git add packages/core/src/folio_core/ && git commit -m "docs: translate folio-core to English"`

### Task 2: Translate Sync Package

**Files:**
- Modify: `packages/doc-sync/src/folio_sync/indexer.py`
- Modify: `packages/doc-sync/src/folio_sync/handler.py`
- Modify: `packages/doc-sync/src/folio_sync/s3_client.py`

- [ ] **Step 1: Translate `indexer.py` docstrings**
  Translate "Orquestra core (puro) + DB (shell) para indexação" and others.
- [ ] **Step 2: Translate `handler.py` (sync) docstrings**
  Translate Lambda handler comments.
- [ ] **Step 3: Translate `s3_client.py` docstrings**
  Translate "todo I/O aqui" and others.
- [ ] **Step 4: Run tests**
  Run: `uv run pytest packages/doc-sync/tests/`
- [ ] **Step 5: Commit**
  Run: `git add packages/doc-sync/src/folio_sync/ && git commit -m "docs: translate folio-sync to English"`

### Task 3: Refactor MCP Handler (Facade + Bilingual)

**Files:**
- Modify: `packages/mcp-server/src/folio_mcp/handler.py`

- [ ] **Step 1: Update imports and initialize FastMCP globally**
  Refactor to move `mcp = FastMCP(...)` to module level and use decorators.
- [ ] **Step 2: Implement `list_topics` facade with bilingual docstring**
```python
@mcp.tool()
async def list_topics():
    """
    [EN] List available documentation topics. Use this to discover the internal vocabulary.
    [PT-BR] Lista os tópicos disponíveis na documentação. Use para descobrir o vocabulário interno.
    """
    return await list_topics_impl()
```
- [ ] **Step 3: Implement `search_docs` facade with bilingual docstring**
```python
@mcp.tool()
async def search_docs(query: str, limit: int = 10):
    """
    [EN] Search documents by terms. Returns ranked paths and snippets.
    [PT-BR] Busca documentos por termos. Retorna caminhos e trechos rankeados.

    Args:
        query: [EN] Search terms. [PT-BR] Termos de busca.
        limit: [EN] Max results (1-50). [PT-BR] Máximo de resultados (1-50).
    """
    return await search_docs_impl(query, limit)
```
- [ ] **Step 4: Implement `get_document` facade with bilingual docstring**
```python
@mcp.tool()
async def get_document(path: str):
    """
    [EN] Retrieve the full content of a document by its path.
    [PT-BR] Recupera o conteúdo integral de um documento pelo seu caminho.

    Args:
        path: [EN] Document path. [PT-BR] Caminho do documento.
    """
    return await get_document_impl(path)
```
- [ ] **Step 5: Update `lambda_handler` and `main`**
  Ensure they work with the new structure.
- [ ] **Step 6: Run MCP tests**
  Run: `uv run pytest packages/mcp-server/tests/test_mcp_handler.py`
- [ ] **Step 7: Commit**
  Run: `git add packages/mcp-server/src/folio_mcp/handler.py && git commit -m "feat: implement bilingual MCP facade"`

### Task 4: Translate MCP Tools Implementation

**Files:**
- Modify: `packages/mcp-server/src/folio_mcp/tools/list_topics.py`
- Modify: `packages/mcp-server/src/folio_mcp/tools/search_docs.py`
- Modify: `packages/mcp-server/src/folio_mcp/tools/get_document.py`

- [ ] **Step 1: Translate `list_topics.py` implementation docstrings**
  Convert the internal docstrings to English only (bilingual is in the facade).
- [ ] **Step 2: Translate `search_docs.py` implementation docstrings**
  Convert to English only.
- [ ] **Step 3: Translate `get_document.py` implementation docstrings**
  Convert to English only.
- [ ] **Step 4: Final validation**
  Run all tests in the workspace: `uv run pytest`
- [ ] **Step 5: Commit**
  Run: `git add packages/mcp-server/src/folio_mcp/tools/ && git commit -m "docs: translate MCP tool implementations to English"`
