FROM python:3.14-rc-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN pip install uv

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY . /app

RUN chown -R appuser:appuser /app

RUN uv sync --frozen --package folio-sync

USER appuser

CMD ["uv", "run", "folio-sync"]
