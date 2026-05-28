"""CLI entrypoint for standalone Folio indexing."""

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

import structlog
from folio_embeddings import create_embedder

from folio_sync.shell.config import settings
from folio_sync.shell.db import SQLiteDocumentRepository, connect_db, init_db

logger = structlog.get_logger()


def main():
    """Run the main CLI indexer logic."""
    parser = argparse.ArgumentParser(description="Indexador de documentos para o Folio Standalone")
    parser.add_argument("data_dir", type=Path, help="Diretório contendo os arquivos .md")
    parser.add_argument("db_path", type=Path, help="Caminho do arquivo SQLite de destino")
    args = parser.parse_args()

    data_dir = args.data_dir
    db_path = args.db_path

    if not data_dir.exists() or not data_dir.is_dir():
        logger.error("cli.data_dir_not_found", data_dir=str(data_dir))
        sys.exit(1)

    provider = settings.get("embedder.provider", "none")
    model = settings.get("embedder.model", "")
    preferred_size = int(settings.get("sync.chunk_size", 512))
    max_size = int(settings.get("sync.chunk_max_size", 1024))

    embedder = create_embedder(
        provider,
        model,
        base_url=settings.get("embedder.ollama_host"),
        timeout=float(settings.get("embedder.ollama_timeout", 60.0)),
        api_key=settings.get("embedder.api_key"),
    )
    logger.info(
        "cli.embedder", provider=provider, model=embedder.model_id, dimensions=embedder.dimensions
    )

    init_db(db_path, embedder)

    stats = {"scanned": 0, "indexed": 0, "skipped": 0}

    with connect_db(db_path) as conn:
        repo = SQLiteDocumentRepository(
            conn,
            embedder,
            chunk_size=preferred_size,
            chunk_max_size=max_size,
        )
        for md_file in data_dir.rglob("*.md"):
            stats["scanned"] += 1
            rel_path = str(md_file.relative_to(data_dir))
            try:
                raw_content = md_file.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.error("file.read_error", path=rel_path, error=str(e))
                continue

            changed = repo.upsert_document(rel_path, raw_content)
            if changed:
                stats["indexed"] += 1
                logger.info("doc.indexed", path=rel_path)
            else:
                stats["skipped"] += 1

        repo.write_meta("embedder_model", embedder.model_id)
        repo.write_meta("chunk_size", str(preferred_size))
        repo.write_meta("chunk_max_size", str(max_size))
        repo.write_meta("indexed_at", datetime.now(UTC).isoformat())

        conn.commit()

    logger.info("sync.full_complete", **stats)


if __name__ == "__main__":
    main()
