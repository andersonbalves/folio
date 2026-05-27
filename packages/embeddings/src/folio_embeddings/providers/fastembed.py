"""FastEmbedEmbedder — in-process ONNX embedder via the fastembed package."""

from __future__ import annotations

from typing import Any


class FastEmbedEmbedder:
    """Embedder backed by fastembed (ONNX in-process, no network required).

    The ``fastembed`` package is an optional dependency; it is imported lazily
    inside methods so the module can be loaded even when fastembed is not
    installed.
    """

    def __init__(self, model: str = "BAAI/bge-small-en-v1.5") -> None:
        """Initialise the embedder.

        Args:
            model: fastembed model name, e.g. ``'BAAI/bge-small-en-v1.5'``.
        """
        self._model = model
        self._instance: Any = None
        self._dimensions: int | None = None

    def _get_instance(self) -> Any:
        if self._instance is None:
            try:
                from fastembed import TextEmbedding  # type: ignore[import-untyped]  # ty: ignore[unresolved-import]  # noqa: I001
            except ImportError as exc:
                raise ImportError(
                    "fastembed is required for FastEmbedEmbedder. "
                    "Install it with: uv add folio-embeddings[fastembed]"
                ) from exc
            self._instance = TextEmbedding(model_name=self._model)
            # Cache dimensions from the model metadata.
            self._dimensions = int(self._instance.dim)
        return self._instance

    @property
    def model_id(self) -> str:
        """Return the provider-qualified model identifier."""
        return f"fastembed:{self._model}"

    @property
    def dimensions(self) -> int:
        """Return vector dimensions, instantiating the model lazily if needed."""
        if self._dimensions is None:
            # Instantiate the model to resolve dimensions.
            self._get_instance()
        assert self._dimensions is not None
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts using the fastembed ONNX model.

        Args:
            texts: Input strings to embed.

        Returns:
            One float vector per input text.
        """
        instance = self._get_instance()
        embeddings = instance.embed(texts)
        return [list(map(float, vec)) for vec in embeddings]
