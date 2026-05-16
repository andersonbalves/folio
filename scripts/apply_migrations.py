"""Aplica migrations no banco de dados local."""

from pathlib import Path

import psycopg
from folio_sync.config import settings

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def get_connection():
    return psycopg.connect(
        host=settings.database.host,
        port=settings.database.port,
        dbname=settings.database.name,
        user=settings.database.user,
        password=settings.database.password,
        autocommit=True,
    )


def apply_migrations():
    try:
        with get_connection() as conn, conn.cursor() as cur:
            files = sorted(MIGRATIONS_DIR.glob("*.sql"))
            for file in files:
                sql = file.read_text()
                cur.execute(sql)
    except Exception:
        exit(1)


if __name__ == "__main__":
    apply_migrations()
