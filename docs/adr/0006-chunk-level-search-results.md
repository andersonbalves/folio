# 0006. Search tools return chunks, not documents

All three search tools (`lexical_search`, `semantic_search`, `hybrid_search`) return Chunks as their result unit, not Documents. Each result includes `doc_path`, `heading_path`, `chunk_index`, `content`, and `rank`.

Documents can be large and cover multiple unrelated concepts. Returning the full document per result gives the LLM more tokens than necessary and obscures which part of the document is actually relevant. A Chunk result with its Heading Path gives precise context: the LLM receives the exact passage that matched, knows where it lives in the document, and can call `get_document` if it needs the full surrounding content.

A consequence: multiple chunks from the same document may appear in a single result set. This is intentional — it signals strong relevance rather than being suppressed by deduplication.
