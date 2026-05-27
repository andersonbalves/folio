# Glossary

## Deployment

**Standalone**: A deployment mode where the application and its data exist as an **Immutable Artifact**. Both the documents and the pre-indexed SQLite database are baked into the Docker image at build time. There is no external dependency on S3 or PostgreSQL, and no runtime data ingestion.

## Indexing

**Document**: A single Markdown file ingested by folio-sync. The atomic unit of ingestion and retrieval via `get_document`.
_Avoid_: File, page, article

**Chunk**: A semantic subdivision of a Document, bounded by heading structure and paragraph boundaries. Never split inside a fenced code block. The unit of indexing for both lexical and semantic search.
_Avoid_: Fragment, segment, piece

**Heading Path**: The ordered trail of parent headings that locates a Chunk within its Document (e.g., "Workloads > Pods > Liveness Probes").
_Avoid_: Breadcrumb, section path, heading trail

**Embedder**: A configurable component that converts text into a dense vector. Selected via `FOLIO_EMBEDDER` env var. Must be the same provider at both index time and query time — a mismatch causes an explicit startup error.
_Avoid_: Encoder, vectorizer, embedding model

**Embedding**: The dense vector representation of a Chunk or query string, used for cosine similarity ranking in semantic search.
_Avoid_: Vector, feature vector

## Search

**Lexical Search**: BM25 full-text search over chunk content via SQLite FTS5. Does not require an Embedder. Exposed as the `lexical_search` MCP tool.
_Avoid_: Full-text search, keyword search, `search_docs` (old name)

**Semantic Search**: Cosine similarity search over chunk embeddings via sqlite-vec. Requires an Embedder configured. Exposed as the `semantic_search` MCP tool.
_Avoid_: Vector search, embedding search

**Hybrid Search**: Combines Lexical Search and Semantic Search rankings using Reciprocal Rank Fusion (k=60). Fails explicitly when no Embedder is configured. Exposed as the `hybrid_search` MCP tool.
_Avoid_: Combined search, unified search

**RRF (Reciprocal Rank Fusion)**: The merging formula used by Hybrid Search: `score = 1/(k + rank_lexical) + 1/(k + rank_semantic)` where `k=60`. Produces a single ranked list from two independent result sets.

## Example dialogue

> **Dev**: I want to find all docs about Pod scheduling.
> **Domain expert**: Use `lexical_search` for exact terms like "nodeSelector" or "affinity". Use `semantic_search` for concepts like "how to keep pods on the same node". Use `hybrid_search` when you're not sure — it combines both.
>
> **Dev**: The results come back as chunks, not full docs?
> **Domain expert**: Yes. Each result is a Chunk with its Heading Path so you know where it sits in the Document. If you need the full context, call `get_document` with the `doc_path`.
>
> **Dev**: What if semantic search isn't configured?
> **Domain expert**: `semantic_search` and `hybrid_search` fail with a clear error. `lexical_search` always works — it has no dependency on an Embedder.
