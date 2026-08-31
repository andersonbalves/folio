FROM python:3.14-rc-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN pip install uv

WORKDIR /app
COPY . /app

RUN uv sync --frozen --package folio-sync

RUN groupadd -r appuser && useradd -r -g appuser appuser && chown -R appuser:appuser /app
USER appuser

CMD ["uv", "run", "folio-sync"]
