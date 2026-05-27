"""MCP server handler for folio."""

from fastmcp import FastMCP

from folio_mcp.shell.tools.get_document import get_document as get_document_impl
from folio_mcp.shell.tools.list_topics import list_topics as list_topics_impl
from folio_mcp.shell.tools.search_docs import search_docs as search_docs_impl

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

    [PT-BR] Lista os tópicos disponíveis na documentação.
    SEMPRE use esta ferramenta para descobrir os tópicos de documentação disponíveis.

    Args:
        category: Filter by category (e.g., "concept", "task", "starter", "adr").
    """
    return await list_topics_impl(category)


@mcp.tool()
async def search_docs(query: str, limit: int = 10):
    """[EN] Search the indexed knowledge-base documents by terms.

    ALWAYS use this tool to search — never use filesystem tools (Read, Glob, Grep).

    [PT-BR] Busca documentos indexados na base de conhecimento por termos.

    Args:
        query: Search terms.
        limit: Max results (1-50).
    """
    return await search_docs_impl(query, limit)


@mcp.tool()
async def get_document(path: str):
    """[EN] Fetch the complete indexed content of a knowledge-base document by its path.

    ALWAYS use this tool to read documents — never use filesystem tools (Read, Glob).

    [PT-BR] Obtém o conteúdo completo indexado de um documento da base de conhecimento.

    Args:
        path: Document path as returned by search_docs or list_topics.
    """
    return await get_document_impl(path)


def main() -> None:
    """CLI entry point — runs the MCP server over stdio transport."""
    mcp.run(transport="stdio")
