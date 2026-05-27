"""NoneEmbedder — placeholder when no embedder is configured."""

from folio_embeddings.protocol import EmbedderNotConfiguredError


class NoneEmbedder:
    """Placeholder when FOLIO_EMBEDDER=none. All operations raise EmbedderNotConfiguredError."""

    model_id: str = "none"
    dimensions: int = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Raise EmbedderNotConfiguredError unconditionally.

        Args:
            texts: Ignored — always raises.

        Raises:
            EmbedderNotConfiguredError: Always.
        """
        raise EmbedderNotConfiguredError(
            "No embedder configured. Set FOLIO_MCP_EMBEDDER=fastembed|ollama|openai "
            "and FOLIO_MCP_EMBEDDER_MODEL=<model> to enable semantic search."
        )
