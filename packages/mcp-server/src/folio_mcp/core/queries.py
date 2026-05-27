"""Pure SQL query builders. No I/O — return (sql_string, params) tuples."""

from typing import LiteralString, cast


def search_docs_sql(max_fragments: int, max_words: int) -> LiteralString:
    """Return parameterized BM25 search SQL for SQLite FTS5. Bind params: (query, limit)."""
    return cast(
        LiteralString,
        """
        SELECT
            path, title,
            bm25(documents_fts) AS rank,
            snippet(documents_fts, 2, '<mark>', '</mark>', '...', 64) AS snippet
        FROM documents_fts
        WHERE documents_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
    )


def list_topics_sql(category: str | None) -> tuple[LiteralString, tuple]:
    """Return (sql, params) for listing topics, optionally filtered by category."""
    if category:
        return (
            cast(
                LiteralString,
                "SELECT slug, title, description, category, doc_path, sort_order"
                " FROM topics WHERE category = ? ORDER BY category, sort_order, title",
            ),
            (category,),
        )
    return (
        cast(
            LiteralString,
            "SELECT slug, title, description, category, doc_path, sort_order"
            " FROM topics ORDER BY category, sort_order, title",
        ),
        (),
    )


def get_document_sql() -> LiteralString:
    """Return SQL for fetching a single document by path. Bind param: (path,)."""
    return cast(
        LiteralString,
        "SELECT path, title, content, metadata FROM documents WHERE path = ?",
    )
