# 0003. Auto-inicialização do Schema SQLite no folio-sync

## Context

As part of the Standalone migration, we are moving from PostgreSQL to an embedded SQLite database (`sqlite-vec`). The database is generated from scratch as an immutable artifact during the Docker build process. We needed to decide where the schema creation (`CREATE TABLE`) logic should live, given that we are deleting the `infra/migrations/` PostgreSQL folder.

## Decision

We decided to embed the SQLite schema creation directly within the `folio-sync` script (Auto-initialization). When the ingestion script runs, it will ensure the tables exist (`CREATE TABLE IF NOT EXISTS`) before proceeding with data insertion.

## Consequences

- **Pros**: Simplifies the Dockerfile and the build process. No need for external tools (like the `sqlite3` CLI) or a separate migration step in the build pipeline.
- **Cons**: If we ever return to a persistent infrastructure model (e.g., PostgreSQL or a persistent networked SQLite), we will lack a rigorous migration tracking system (like Alembic) for schema evolution. This is acceptable for now because the database is strictly treated as an immutable build artifact.
