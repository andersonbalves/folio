from pydantic import BaseModel


class ParsedMarkdown(BaseModel):
    front_matter: dict
    body: str


class Document(BaseModel):
    path: str
    title: str
    content: str
    content_hash: str
    metadata: dict


class Topic(BaseModel):
    slug: str
    title: str
    description: str
    category: str
    doc_path: str
    sort_order: int


class SearchMatch(BaseModel):
    path: str
    title: str
    snippet: str
    rank: float


class ListTopicsResult(BaseModel):
    topics: list[Topic]
    total: int


class SearchDocsResult(BaseModel):
    matches: list[SearchMatch]
    query: str


class GetDocumentResult(BaseModel):
    path: str
    title: str
    content: str
    metadata: dict
