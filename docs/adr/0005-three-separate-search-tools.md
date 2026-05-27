# 0005. Three separate search tools instead of one unified search

The MCP server exposes three distinct search tools — `lexical_search`, `semantic_search`, and `hybrid_search` — rather than a single `search_docs` tool with a `mode` parameter or a transparent hybrid.

The key driver is graceful degradation: `lexical_search` works with no Embedder configured (the default). A transparent hybrid would fail silently or degrade to BM25 without the LLM knowing — misleading the caller about what ranking was actually applied. Three explicit tools make the contract clear: the LLM chooses based on what it needs, and `semantic_search`/`hybrid_search` fail with an actionable error when no Embedder is configured.

`search_docs` (the original BM25 tool) is renamed to `lexical_search` as part of this change. This is a breaking change to the MCP API, accepted because folio is a standalone artifact with no external API consumers.
