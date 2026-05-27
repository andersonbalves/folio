"""Factory function for creating Embedder instances."""

from folio_embeddings.protocol import Embedder
from folio_embeddings.providers.fastembed import FastEmbedEmbedder
from folio_embeddings.providers.none import NoneEmbedder
from folio_embeddings.providers.ollama import OllamaEmbedder
from folio_embeddings.providers.openai import OpenAIEmbedder


def create_embedder(provider: str, model: str) -> Embedder:
    """Create an Embedder from a provider name and model string.

    Args:
        provider: One of ``'none'``, ``'ollama'``, ``'fastembed'``, ``'openai'``.
        model: Provider-specific model name, e.g. ``'BAAI/bge-small-en-v1.5'``.

    Returns:
        A configured :class:`~folio_embeddings.protocol.Embedder` instance.
        Returns :class:`~folio_embeddings.providers.none.NoneEmbedder` when
        ``provider == 'none'``.

    Raises:
        ValueError: When an unknown provider is specified.
    """
    match provider:
        case "none":
            return NoneEmbedder()
        case "ollama":
            return OllamaEmbedder(model=model)
        case "fastembed":
            return FastEmbedEmbedder(model=model)
        case "openai":
            return OpenAIEmbedder(model=model)
        case _:
            raise ValueError(
                f"Unknown embedder provider: {provider!r}. "
                "Expected one of: 'none', 'ollama', 'fastembed', 'openai'."
            )
