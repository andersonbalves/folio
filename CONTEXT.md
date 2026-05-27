# Glossary

## Standalone

A deployment mode where the application and its data exist as an **Immutable Artifact**. Both the documents and the pre-indexed SQLite database are baked into the Docker image at build time. There is no external dependency on S3 or PostgreSQL, and no runtime data ingestion.
