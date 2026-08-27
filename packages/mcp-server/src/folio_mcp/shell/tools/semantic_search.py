"""Tool: semantic_search. Cosine similarity over chunk embeddings via sqlite-vec."""

import struct

from folio_core.models import ChunkMatch, SemanticSearchResult

from folio_mcp.shell.config import settings
from folio_mcp.shell.db import conn, get_embedder


def semantic_search(query: str, limit: int = 10) -> SemanticSearchResult:
    """Search indexed chunks by semantic similarity.

    Requires an embedder to be configured (FOLIO_EMBEDDER != none).
    Raises an error if no embedder is configured — use lexical_search instead.

    Args:
        query: Natural language description of what you are looking for.
        limit: Maximum number of results (1-50).
    """
    limit = min(max(limit, 1), settings.get("search.max_limit", 50))
    embedder = get_embedder()

    # This raises EmbedderNotConfiguredError if FOLIO_EMBEDDER=none
    vectors = embedder.embed([query])
    query_vector = vectors[0]
    query_blob = struct.pack(f"{len(query_vector)}f", *query_vector)

    sql = """
        SELECT ce.chunk_id, 1.0 - ce.distance AS rank
        FROM chunk_embeddings ce
        WHERE ce.embedding MATCH ? AND k = ?
        ORDER BY ce.distance ASC
    """
    with conn() as c_conn:
        cur = c_conn.cursor()
        cur.execute(sql, (query_blob, limit))
        vec_rows = cur.fetchall()

        if not vec_rows:
            return SemanticSearchResult(matches=[], query=query)

        chunk_ids = [r["chunk_id"] for r in vec_rows]
        rank_by_id = {r["chunk_id"]: float(r["rank"]) for r in vec_rows}

        placeholders = ",".join("?" * len(chunk_ids))
        sql_chunks = (
            f"SELECT id, doc_path, heading_path, chunk_index, content "  # nosec B608 # nosemgrep
            f"FROM chunks WHERE id IN ({placeholders})"
        )
        cur.execute(sql_chunks, chunk_ids)
        chunk_rows = {r["id"]: r for r in cur.fetchall()}

    matches = []
    for chunk_id in chunk_ids:
        if chunk_id in chunk_rows:
            r = chunk_rows[chunk_id]
            matches.append(
                ChunkMatch(
                    doc_path=r["doc_path"],
                    heading_path=r["heading_path"],
                    chunk_index=r["chunk_index"],
                    content=r["content"],
                    rank=rank_by_id[chunk_id],
                )
            )

    return SemanticSearchResult(matches=matches, query=query)
