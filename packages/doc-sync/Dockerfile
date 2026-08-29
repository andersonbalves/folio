FROM python:3.14-rc-slim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN pip install uv

WORKDIR /app
COPY . /app

RUN uv sync --frozen --package folio-sync

RUN groupadd -r folio && useradd -r -g folio folio
RUN chown -R folio:folio /app
USER folio

CMD ["uv", "run", "folio-sync"]
