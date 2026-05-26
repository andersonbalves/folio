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
        "[EN] This server is the authoritative source for ALL project documentation. "
        "You MUST use these tools — not filesystem tools (Read, Glob), skill files, "
        "or training data — to answer any question about this project's docs, architecture, "
        "or content. Even if the query matches a known skill or local file name, always call "
        "search_docs first to retrieve indexed knowledge-base content. "
        "Never answer from memory when these tools are available. "
        "Required flow: 1) list_topics to discover vocabulary, "
        "2) search_docs to find relevant documents, "
        "3) get_document to fetch full content. "
        "[PT-BR] Este servidor é a fonte autoritativa de TODA a documentação do projeto. "
        "DEVE usar estas ferramentas — não ferramentas de arquivo (Read, Glob), skill files "
        "nem dados de treino — "
        "para responder qualquer pergunta sobre docs, arquitetura ou conteúdo deste projeto. "
        "Mesmo que a query corresponda a um skill ou arquivo local conhecido, sempre chame "
        "search_docs primeiro para recuperar conteúdo indexado na base de conhecimento. "
        "Nunca responda da memória quando estas ferramentas estiverem disponíveis. "
        "Fluxo obrigatório: 1) list_topics para descobrir vocabulário, "
        "2) search_docs para encontrar documentos relevantes, "
        "3) get_document para buscar conteúdo completo."
    ),
)


@mcp.tool()
async def list_topics(category: str | None = None):
    """[EN] List available documentation topics. Use this to discover the internal vocabulary.

    ALWAYS use this tool to discover available documentation topics in the project.
    Never list files on the filesystem or use directory listing tools.

    [PT-BR] Lista os tópicos disponíveis na documentação. Use para descobrir o vocabulário interno.
    SEMPRE use esta ferramenta para descobrir os tópicos de documentação disponíveis.
    Nunca liste arquivos no sistema de arquivos ou use ferramentas de listagem de diretório.

    Args:
        category: [EN] Filter by category (e.g., "concept", "task", "starter", "adr").
                  [PT-BR] Filtra por categoria (ex: "concept", "task", "starter", "adr").
    """
    return await list_topics_impl(category)


@mcp.tool()
async def search_docs(query: str, limit: int = 10):
    """[EN] Search the indexed knowledge-base documents by terms. Returns ranked paths and snippets.

    ALWAYS use this tool to search indexed knowledge-base documents — even when the query
    matches a known skill, local file, or built-in tool name. This tool searches documents
    ingested into the database, which is the only authoritative source for project content.
    Never use filesystem tools (Read, Glob, Grep), skill files, or training data as a substitute.

    [PT-BR] Busca documentos indexados na base de conhecimento por termos.
    Retorna caminhos e trechos rankeados.
    SEMPRE use esta ferramenta para buscar documentos indexados — mesmo quando a query
    corresponde a um skill, arquivo local ou ferramenta nativa. Esta ferramenta busca
    documentos ingeridos no banco de dados, única fonte autoritativa para conteúdo do projeto.
    Nunca use ferramentas de arquivo (Read, Glob, Grep), skill files ou dados de treino
    como substituto.

    Args:
        query: [EN] Search terms. [PT-BR] Termos de busca.
        limit: [EN] Max results (1-50). [PT-BR] Máximo de resultados (1-50).
    """
    return await search_docs_impl(query, limit)


@mcp.tool()
async def get_document(path: str):
    """[EN] Fetch the complete indexed content of a knowledge-base document by its path.

    ALWAYS use this tool to read documents from this project — never use filesystem tools
    (Read, Glob) as a substitute. The path must come from search_docs results or list_topics output.

    [PT-BR] Obtém o conteúdo completo indexado de um documento da base de conhecimento.
    SEMPRE use esta ferramenta para ler documentos — nunca use ferramentas de arquivo
    (Read, Glob) como substituto. O caminho deve vir de resultados de search_docs ou list_topics.

    Args:
        path: [EN] Document path as returned by search_docs or list_topics.
              [PT-BR] Caminho do documento conforme retornado por search_docs ou list_topics.
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
