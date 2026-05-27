"""OpenAIEmbedder — embedder backed by the OpenAI REST API."""

from __future__ import annotations

import os
from typing import Any

# Known output dimensions for OpenAI embedding models.
_OPENAI_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


class OpenAIEmbedder:
    """Embedder backed by the OpenAI embeddings API.

    The ``openai`` package is an optional dependency; it is imported lazily
    inside methods so the module can be loaded even when openai is not
    installed.

    The ``OPENAI_API_KEY`` environment variable must be set.
    """

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        """Initialise the embedder.

        Args:
            model: OpenAI embedding model name, e.g. ``'text-embedding-3-small'``.
        """
        self._model = model
        self._api_key: str | None = os.environ.get("OPENAI_API_KEY")

    def _get_client(self) -> Any:
        try:
            import openai as _openai
        except ImportError as exc:
            raise ImportError(
                "openai is required for OpenAIEmbedder. "
                "Install it with: uv add folio-embeddings[openai]"
            ) from exc
        return _openai.OpenAI(api_key=self._api_key)

    @property
    def model_id(self) -> str:
        """Return the provider-qualified model identifier."""
        return f"openai:{self._model}"

    @property
    def dimensions(self) -> int:
        """Return the known output dimension for this OpenAI model."""
        return _OPENAI_DIMENSIONS.get(self._model, 1536)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts via the OpenAI embeddings API.

        Args:
            texts: Input strings to embed.

        Returns:
            One float vector per input text.
        """
        client = self._get_client()
        response = client.embeddings.create(input=texts, model=self._model)
        return [item.embedding for item in response.data]
