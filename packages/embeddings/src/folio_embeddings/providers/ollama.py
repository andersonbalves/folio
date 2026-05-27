"""OllamaEmbedder — HTTP embedder using the Ollama API."""

import os

import httpx


class OllamaEmbedder:
    """Embedder backed by the Ollama local HTTP API.

    Calls POST /api/embeddings for each text individually (Ollama does not
    support native batching).  The ``dimensions`` property is resolved lazily
    on the first call to ``embed()``.
    """

    def __init__(
        self,
        model: str,
        base_url: str | None = None,
    ) -> None:
        """Initialise the embedder.

        Args:
            model: Ollama model name, e.g. ``'nomic-embed-text'``.
            base_url: Base URL of the Ollama HTTP server. Defaults to the
                ``OLLAMA_HOST`` environment variable, or
                ``'http://localhost:11434'`` if unset.
        """
        self._model = model
        self._base_url = (
            base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        ).rstrip("/")
        self._dimensions: int | None = None

    @property
    def model_id(self) -> str:
        """Return the provider-qualified model identifier."""
        return f"ollama:{self._model}"

    @property
    def dimensions(self) -> int:
        """Return vector dimensions, probing the model lazily if needed."""
        if self._dimensions is None:
            # Embed a single space to discover the vector size.
            vectors = self._embed_single(" ")
            self._dimensions = len(vectors)
        return self._dimensions

    def _embed_single(self, text: str) -> list[float]:
        response = httpx.post(
            f"{self._base_url}/api/embeddings",
            json={"model": self._model, "prompt": text},
            timeout=60.0,
        )
        response.raise_for_status()
        data: dict[str, object] = response.json()
        if "error" in data:
            raise ValueError(f"Ollama API error: {data['error']}")
        embedding = data.get("embedding")
        if not isinstance(embedding, list):
            raise ValueError(f"Unexpected embedding format from Ollama: {embedding}")
        return [float(v) for v in embedding]

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts via individual Ollama API calls.

        Args:
            texts: Input strings to embed.

        Returns:
            One float vector per input text.
        """
        results: list[list[float]] = []
        for text in texts:
            vector = self._embed_single(text)
            results.append(vector)
        # Cache dimensions from the first real batch.
        if self._dimensions is None and results:
            self._dimensions = len(results[0])
        return results
