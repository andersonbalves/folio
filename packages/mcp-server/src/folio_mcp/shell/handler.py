"""MCP server handler for folio."""

from fastmcp import FastMCP

from folio_mcp.shell.tools.get_document import get_document as get_document_impl
from folio_mcp.shell.tools.hybrid_search import hybrid_search as hybrid_search_impl
from folio_mcp.shell.tools.lexical_search import lexical_search as lexical_search_impl
from folio_mcp.shell.tools.list_topics import list_topics as list_topics_impl
from folio_mcp.shell.tools.semantic_search import semantic_search as semantic_search_impl

mcp = FastMCP(
    name="folio",
    instructions=(
        "[EN] This server is the authoritative source for ALL project documentation. "
        "Use these tools — never filesystem tools. "
        "Recommended search flow: "
        "1) list_topics to discover vocabulary, "
        "2) hybrid_search (if embedder configured) or lexical_search for keywords, "
        "   semantic_search for concepts using different vocabulary, "
        "3) get_document to fetch full document when needed. "
        "Search results are at chunk level — each result is a passage with its heading path. "
        "[PT-BR] Este servidor é a fonte autoritativa de TODA a documentação do projeto. "
        "Use estas ferramentas — nunca ferramentas de arquivo. "
        "Fluxo recomendado: "
        "1) list_topics para descobrir vocabulário, "
        "2) hybrid_search (se embedder configurado) ou lexical_search para termos, "
        "   semantic_search para conceitos com vocabulário diferente, "
        "3) get_document para buscar documento completo quando necessário."
    ),
)


@mcp.tool()
def list_topics(category: str | None = None):
    """[EN] List available documentation topics. Use this to discover the internal vocabulary.

    ALWAYS use this tool to discover available documentation topics in the project.
    Never list files on the filesystem or use directory listing tools.

    [PT-BR] Lista os tópicos disponíveis na documentação.
    SEMPRE use esta ferramenta para descobrir os tópicos de documentação disponíveis.

    Args:
        category: Filter by category (e.g., "concept", "task", "starter", "adr").
    """
    return list_topics_impl(category)


@mcp.tool()
def lexical_search(query: str, limit: int = 10):
    """[EN] BM25 full-text search over indexed document chunks.

    Always available. Best for exact terms, identifiers, and code symbols.
    Results are chunk-level passages with heading context.
    Use semantic_search or hybrid_search for conceptual queries.

    [PT-BR] Busca textual BM25 sobre chunks indexados.

    Args:
        query: Search terms. Supports "exact phrase", OR, -excluded.
        limit: Max results (1-50).
    """
    return lexical_search_impl(query, limit)


@mcp.tool()
def semantic_search(query: str, limit: int = 10):
    """[EN] Semantic similarity search over chunk embeddings.

    Requires FOLIO_EMBEDDER to be configured. Fails with a clear error if not.
    Best for natural language descriptions and conceptual queries.

    [PT-BR] Busca semântica por similaridade sobre embeddings de chunks.

    Args:
        query: Natural language description of what you are looking for.
        limit: Max results (1-50).
    """
    return semantic_search_impl(query, limit)


@mcp.tool()
def hybrid_search(query: str, limit: int = 10):
    """[EN] Combined BM25 + semantic search merged via Reciprocal Rank Fusion.

    Requires FOLIO_EMBEDDER to be configured. Fails with a clear error if not.
    Best overall search mode when embedder is available.

    [PT-BR] Busca híbrida BM25 + semântica com Reciprocal Rank Fusion.

    Args:
        query: Search query — keyword terms or natural language.
        limit: Max results (1-50).
    """
    return hybrid_search_impl(query, limit)


@mcp.tool()
def get_document(path: str):
    """[EN] Fetch the complete indexed content of a knowledge-base document by its path.

    ALWAYS use this tool to read documents — never use filesystem tools (Read, Glob).

    [PT-BR] Obtém o conteúdo completo indexado de um documento da base de conhecimento.

    Args:
        path: Document path as returned by lexical_search, semantic_search, or list_topics.
    """
    return get_document_impl(path)


def main() -> None:
    """CLI entry point — runs the MCP server over stdio transport."""
    mcp.run(transport="stdio")
