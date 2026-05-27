"""folio-embeddings: Embedder protocol and provider implementations for Folio."""

from folio_embeddings.factory import create_embedder
from folio_embeddings.protocol import Embedder, EmbedderNotConfiguredError

__all__ = ["Embedder", "EmbedderNotConfiguredError", "create_embedder"]
