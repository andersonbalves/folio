FROM python:3.14-rc-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PORT=8001

RUN pip install uv

WORKDIR /app
COPY . /app

RUN uv sync --frozen --package folio-mcp

RUN useradd -m appuser && chown -R appuser /app
USER appuser

CMD ["uv", "run", "fastmcp", "run", \
     "packages/mcp-server/src/folio_mcp/shell/handler.py:mcp", \
     "--transport", "sse", "--host", "0.0.0.0", "--port", "8001"]
