FROM python:3.14-rc-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN pip install uv

WORKDIR /app
COPY . /app

RUN groupadd -r appuser && useradd -r -g appuser -m appuser
RUN chown -R appuser:appuser /app
USER appuser

ENV UV_CACHE_DIR=/home/appuser/.cache/uv

RUN uv sync --frozen --package folio-sync

CMD ["uv", "run", "folio-sync"]
