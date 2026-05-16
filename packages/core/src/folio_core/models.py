"""Shared Pydantic models for the folio domain."""

from pydantic import BaseModel


class ParsedMarkdown(BaseModel):
    """Markdown file split into YAML front matter and body text."""

    front_matter: dict
    body: str


class Document(BaseModel):
    """Indexed document stored in the database."""

    path: str
    title: str
    content: str
    content_hash: str
    metadata: dict


class Topic(BaseModel):
    """Topic entry derived from an indexed document."""

    slug: str
    title: str
    description: str
    category: str
    doc_path: str
    sort_order: int


class SearchMatch(BaseModel):
    """Single result from a full-text search query."""

    path: str
    title: str
    snippet: str
    rank: float


class ListTopicsResult(BaseModel):
    """Response from the list_topics tool."""

    topics: list[Topic]
    total: int


class SearchDocsResult(BaseModel):
    """Response from the search_docs tool."""

    matches: list[SearchMatch]
    query: str


class GetDocumentResult(BaseModel):
    """Response from the get_document tool."""

    path: str
    title: str
    content: str
    metadata: dict
