FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock settings.yaml ./
COPY packages/ ./packages/
RUN uv sync --frozen --no-dev

# Fixar cache path para poder copiar no stage runtime
ENV FASTEMBED_CACHE_PATH=/app/.fastembed_cache
# Embedder para indexação — baixa modelo e gera vetores no SQLite
ENV FOLIO_SYNC_EMBEDDER="fastembed"
ENV FOLIO_SYNC_EMBEDDER_MODEL="BAAI/bge-small-en-v1.5"

COPY data/ ./data/

# Indexação baixa modelo fastembed, gera chunks + vetores, salva em FASTEMBED_CACHE_PATH
RUN uv run python packages/doc-sync/src/folio_sync/shell/cli.py ./data/ /app/folio.sqlite

# Stage 2: Runtime
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN groupadd -r folio && useradd -r -g folio folio

# .venv usa editable installs — source dos packages deve estar presente
COPY --chown=folio:folio --from=builder /app/.venv /app/.venv
COPY --chown=folio:folio --from=builder /app/folio.sqlite /app/folio.sqlite
COPY --chown=folio:folio --from=builder /app/.fastembed_cache /app/.fastembed_cache
COPY --chown=folio:folio settings.yaml ./
COPY --chown=folio:folio packages/core ./packages/core
COPY --chown=folio:folio packages/embeddings ./packages/embeddings
COPY --chown=folio:folio packages/mcp-server ./packages/mcp-server

USER folio

ENV PATH="/app/.venv/bin:$PATH"
ENV FOLIO_MCP_DB_PATH="/app/folio.sqlite"
ENV FASTEMBED_CACHE_PATH="/app/.fastembed_cache"
# Embedder padrão — usa o modelo já embutido na imagem
ENV FOLIO_MCP_EMBEDDER="fastembed"
ENV FOLIO_MCP_EMBEDDER_MODEL="BAAI/bge-small-en-v1.5"

EXPOSE 8001

CMD ["fastmcp", "run", "packages/mcp-server/src/folio_mcp/shell/handler.py:mcp"]
