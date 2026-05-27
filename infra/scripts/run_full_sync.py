"""Run a full S3→PostgreSQL sync via the doc-sync CLI entry point."""

from folio_sync.handler import main

if __name__ == "__main__":
    main()
