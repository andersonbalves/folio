"""Factory function for creating Embedder instances."""

from folio_embeddings.protocol import Embedder
from folio_embeddings.providers.fastembed import FastEmbedEmbedder
from folio_embeddings.providers.none import NoneEmbedder
from folio_embeddings.providers.ollama import OllamaEmbedder
from folio_embeddings.providers.openai import OpenAIEmbedder


def create_embedder(
    provider: str,
    model: str,
    *,
    base_url: str | None = None,
    timeout: float = 60.0,
    api_key: str | None = None,
) -> Embedder:
    """Create an Embedder from a provider name and model string.

    Args:
        provider: One of ``'none'``, ``'ollama'``, ``'fastembed'``, ``'openai'``.
        model: Provider-specific model name, e.g. ``'BAAI/bge-small-en-v1.5'``.
        base_url: Ollama server URL. Defaults to ``http://localhost:11434``.
        timeout: HTTP timeout in seconds for Ollama requests.
        api_key: API key for OpenAI. Falls back to ``OPENAI_API_KEY`` env var if ``None``.

    Returns:
        A configured :class:`~folio_embeddings.protocol.Embedder` instance.

    Raises:
        ValueError: When an unknown provider is specified.
    """
    match provider:
        case "none":
            return NoneEmbedder()
        case "ollama":
            return OllamaEmbedder(model=model, base_url=base_url, timeout=timeout)
        case "fastembed":
            return FastEmbedEmbedder(model=model)
        case "openai":
            return OpenAIEmbedder(model=model, api_key=api_key)
        case _:
            raise ValueError(
                f"Unknown embedder provider: {provider!r}. "
                "Expected one of: 'none', 'ollama', 'fastembed', 'openai'."
            )
