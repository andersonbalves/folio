"""Pure mappers: DB rows → Pydantic models. No I/O."""

from folio_core.models import (
    GetDocumentResult,
    ListTopicsResult,
    SearchDocsResult,
    SearchMatch,
    Topic,
)


def map_search_rows(rows: list, query: str) -> SearchDocsResult:
    """Map raw DB rows from search_docs query to SearchDocsResult."""
    matches = [SearchMatch(path=r[0], title=r[1], rank=float(r[2]), snippet=r[3]) for r in rows]
    return SearchDocsResult(matches=matches, query=query)


def map_topic_rows(rows: list) -> ListTopicsResult:
    """Map raw DB rows from list_topics query to ListTopicsResult."""
    topics = [
        Topic(
            slug=r[0],
            title=r[1],
            description=r[2],
            category=r[3],
            doc_path=r[4],
            sort_order=r[5],
        )
        for r in rows
    ]
    return ListTopicsResult(topics=topics, total=len(topics))


def map_document_row(row: tuple | None) -> GetDocumentResult | None:
    """Map a single DB row from get_document query to GetDocumentResult."""
    if row is None:
        return None
    return GetDocumentResult(path=row[0], title=row[1], content=row[2], metadata=row[3])
