# Design Spec: Translation and Bilingual Support

- **Date**: 2026-05-15
- **Topic**: Codebase Translation to English and Bilingual MCP Support
- **Status**: Draft

## Context & Purpose

The `folio` project currently has docstrings, comments, and MCP tool descriptions in Portuguese. To make the project more accessible and follow international standards, all internal code (comments and docstrings) must be in English. Additionally, the MCP (Model Context Protocol) server needs to support both English (EN) and Brazilian Portuguese (PT-BR) so that AI agents and users from both contexts can interact with it effectively.

## Proposed Changes

### 1. Internal Code Translation
All internal documentation within the Python packages will be translated to English.

- **Scope**:
  - `packages/core/src/folio_core/`
  - `packages/doc-sync/src/folio_sync/`
  - `packages/mcp-server/src/folio_mcp/`
- **Actions**:
  - Translate module-level docstrings.
  - Translate class and function docstrings.
  - Translate inline and block comments.
  - Keep variable and function names as they are (already in English).

### 2. Bilingual MCP Support (Facade Pattern)
The MCP server will be refactored to use a "Facade" pattern in `handler.py` with FastMCP decorators.

- **Structure**:
  - `packages/mcp-server/src/folio_mcp/handler.py`: Will contain the `FastMCP` instance and tool definitions decorated with `@mcp.tool()`.
  - These decorated functions will serve as the "Facade", containing bilingual docstrings.
  - The actual logic will still reside in `packages/mcp-server/src/folio_mcp/tools/*.py`.
- **Bilingual Format**:
  - Descriptions and arguments will use tags: `[EN] ... [PT-BR] ...`.
  - Example:
    ```python
    @mcp.tool()
    async def list_topics():
        """
        [EN] List available documentation topics.
        [PT-BR] Lista os tópicos disponíveis na documentação.
        """
        return await list_topics_impl()
    ```

### 3. Architecture Benefits
- **Separation of Concerns**: Implementation logic is decoupled from MCP-specific metadata.
- **Centralized Metadata**: All bilingual strings for the AI agent are in one file (`handler.py`).
- **Standardization**: Uses standard FastMCP decorators while avoiding circular imports by keeping implementation in separate modules.

## Verification Plan

### Automated Tests
- Run existing tests to ensure translation didn't break functionality.
- Add/update tests for `handler.py` to verify MCP server construction with bilingual strings.
- Command: `uv run pytest packages/mcp-server/tests/test_mcp_handler.py`

### Manual Verification
- Inspect the generated MCP tool definitions (e.g., using `mcp list-tools` if applicable or by running the server in stdio mode and checking output).
- Verify that AI agents (like Claude) correctly interpret the bilingual descriptions.
