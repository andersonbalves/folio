# 0001. Ingestion Local via Docker Multi-Stage Build

## Context

We are migrating `folio-mcp` to a Standalone (Immutable Artifact) deployment model, removing the dependency on an external PostgreSQL database and AWS/LocalStack S3. To populate the embedded SQLite database, we need to ingest markdown documents into the database before the application is served.

We debated whether to perform this ingestion via a host-level task (`make index`) or bake it directly into the Docker image build process using multi-stage builds.

## Decision

We will use a **Docker Multi-Stage Build** to perform data ingestion. The first stage will copy the documents into the image and run an ingestion script (`ingest_local.py`) to generate the `sqlite` database. The second stage will copy only the compiled database and the necessary runtime code.

## Consequences

- **Pros**: Strong architectural isolation. The host machine does not need the Python environment or dependencies to build the final database artifact. The entire process is encapsulated in `docker build`.
- **Cons**: Skipping the ingestion step for simple tests relies entirely on Docker's layer caching. If any file referenced in the ingestion script changes (e.g., Python code or a single document), Docker will invalidate the cache and rebuild the database from scratch, making granular "sub-steps" via `make` more difficult to control.
