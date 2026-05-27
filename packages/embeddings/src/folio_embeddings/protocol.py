"""Embedder protocol and shared error types."""

from typing import Protocol, runtime_checkable


class EmbedderNotConfiguredError(RuntimeError):
    """Raised when semantic/hybrid search is called without a configured embedder."""


@runtime_checkable
class Embedder(Protocol):
    """Protocol for text embedding backends used across folio packages."""

    @property
    def model_id(self) -> str:
        """Unique identifier written to meta table, e.g. 'fastembed:BAAI/bge-small-en-v1.5'."""
        ...

    @property
    def dimensions(self) -> int:
        """Vector dimension for schema creation."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns one vector per text."""
        ...
