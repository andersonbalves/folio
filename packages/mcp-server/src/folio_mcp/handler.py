"""MCP server handler for folio — bilingual facade over internal tools."""

import asyncio

from fastmcp import FastMCP

from folio_mcp.db import close_pool, get_pool
from folio_mcp.tools.get_document import get_document as get_document_impl
from folio_mcp.tools.list_topics import list_topics as list_topics_impl
from folio_mcp.tools.search_docs import search_docs as search_docs_impl

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)

mcp = FastMCP(
    name="folio",
    instructions=(
        "[EN] Internal documentation indexed for search. "
        "Recommended flow: 1) list_topics to discover vocabulary, "
        "2) search_docs with exact terms, "
        "3) get_document to read full files. "
        "[PT-BR] Documentação interna indexada para busca. "
        "Fluxo recomendado: 1) list_topics para descobrir vocabulário, "
        "2) search_docs com termos exatos, "
        "3) get_document para ler arquivos completos."
    ),
)


@mcp.tool()
async def list_topics(category: str | None = None):
    """[EN] List available documentation topics. Use this to discover the internal vocabulary.

    [PT-BR] Lista os tópicos disponíveis na documentação. Use para descobrir o vocabulário interno.

    Args:
        category: [EN] Filter by category (e.g., "concept", "task", "starter", "adr").
                  [PT-BR] Filtra por categoria (ex: "concept", "task", "starter", "adr").
    """
    return await list_topics_impl(category)


@mcp.tool()
async def search_docs(query: str, limit: int = 10):
    """[EN] Search documents by terms. Returns ranked paths and snippets.

    [PT-BR] Busca documentos por termos. Retorna caminhos e trechos rankeados.

    Args:
        query: [EN] Search terms. [PT-BR] Termos de busca.
        limit: [EN] Max results (1-50). [PT-BR] Máximo de resultados (1-50).
    """
    return await search_docs_impl(query, limit)


@mcp.tool()
async def get_document(path: str):
    """[EN] Retrieve the full content of a document by its path.

    [PT-BR] Recupera o conteúdo integral de um documento pelo seu caminho.

    Args:
        path: [EN] Document path. [PT-BR] Caminho do documento.
    """
    return await get_document_impl(path)


async def _invoke_tool(tool_name: str, arguments: dict) -> dict:
    """Dispatch a registered tool by name. Used by the Lambda handler."""
    tools = {
        "list_topics": list_topics_impl,
        "search_docs": search_docs_impl,
        "get_document": get_document_impl,
    }
    fn = tools.get(tool_name)
    if fn is None:
        return {"error": f"Tool '{tool_name}' not found"}
    await get_pool()
    result = await fn(**arguments)
    await close_pool()
    if result is None:
        return {"error": "Not found"}

    # result might be a list (list_topics) or a Pydantic model
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return result


def lambda_handler(event: dict, context=None) -> dict:
    """AWS Lambda entry point for direct tool invocation."""
    tool_name = event.get("tool", "")
    arguments = event.get("arguments", {})
    result = _loop.run_until_complete(_invoke_tool(tool_name, arguments))
    return {"statusCode": 200, "body": result}


def main() -> None:
    """CLI entry point — runs the MCP server over stdio transport."""
    mcp.run(transport="stdio")
