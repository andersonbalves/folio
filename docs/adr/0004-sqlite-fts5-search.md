# 0004. Substituição do Postgres tsvector pelo SQLite FTS5

## Context

In migrating the MCP server from a LocalStack PostgreSQL backend to a Standalone embedded SQLite artifact, we must ensure that full-text search capabilities are not lost, since vector embeddings/semantic search will be implemented in a future iteration. The existing `search_docs` queries rely heavily on PostgreSQL-specific functions (`ts_rank_cd`, `ts_headline`, `websearch_to_tsquery`, and `tsvector` columns).

## Decision

We will migrate the search index to **SQLite FTS5 (Full-Text Search 5) Virtual Tables**. We will map the queries to use the `MATCH` operator, and replace PostgreSQL text processing with FTS5's built-in `bm25()` scoring and `snippet()` text highlighting functions.

## Consequences

- **Pros**: Maintains BM25 ranking and search-term highlighting. Performance is extremely high for embedded databases. Eliminates the need to wait for the vector search implementation.
- **Cons**: Minor dialect differences between Postgres' `websearch_to_tsquery` (which handles boolean operators very robustly) and SQLite's FTS5 syntax parser. We will need to sanitize user input slightly to avoid syntax errors in the FTS5 query parser.
