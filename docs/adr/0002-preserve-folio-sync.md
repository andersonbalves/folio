# 0002. Preservar o pacote folio-sync para indexação

## Context

With the migration to a Standalone model and the removal of LocalStack (SQS/S3), the `folio-sync` package's original trigger mechanism became obsolete. We considered deleting the package entirely and merging its pure functions into `folio-mcp`.

## Decision

We will **preserve the `folio-sync` package** as a standalone module responsible for orchestration and execution of the indexing process. Its *shell* layer will be rewritten to operate as a local CLI/batch process instead of listening to AWS SQS events.

## Consequences

- **Pros**: Maintains a clean bounded context for the ingestion pipeline. As the pipeline grows in complexity (e.g., adding LLM embeddings and semantic search in the future), `folio-sync` will encapsulate this logic without bloating the `folio-mcp` server.
- **Cons**: Requires rewriting the `folio-sync/shell` layer to read from local file system instead of S3, and removing all `boto3` and SQS handler code.
