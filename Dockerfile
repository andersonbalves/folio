FROM python:3.14-slim AS builder

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Instalar dependências (com cache)
COPY pyproject.toml uv.lock ./
COPY packages/ ./packages/
RUN uv sync --frozen --no-dev

# Copiar dados para indexação
COPY data/ ./data/

# Executar indexação para criar o banco de dados sqlite
RUN uv run python packages/doc-sync/src/folio_sync/shell/cli.py ./data/ /app/folio.sqlite

# Stage 2: Runtime
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copiar apenas dependências e código necessários
COPY --chown=folio:folio --from=builder /app/.venv /app/.venv
COPY --chown=folio:folio --from=builder /app/folio.sqlite /app/folio.sqlite
COPY pyproject.toml uv.lock ./
COPY packages/core ./packages/core
COPY packages/mcp-server ./packages/mcp-server

RUN groupadd -r folio && useradd -r -g folio folio
USER folio

# Garantir que usamos o ambiente virtual criado
ENV PATH="/app/.venv/bin:$PATH"
ENV FOLIO_MCP_DB_PATH="/app/folio.sqlite"

# Expor a porta caso deseje usar sse transport (opcional, por padrão usa stdio para MCP)
EXPOSE 8001

# Rodar o fastmcp handler
CMD ["fastmcp", "run", "packages/mcp-server/src/folio_mcp/shell/handler.py:mcp"]
