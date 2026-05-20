# Design Doc: Translate Sync Package to English

**Status:** APPROVED
**Topic:** Translation of `packages/doc-sync/` to English.

## 1. Purpose
The goal is to translate all remaining Portuguese docstrings and comments in the `packages/doc-sync/` package to English to maintain consistency across the codebase, as variables and function names are already in English.

## 2. Scope
The following files will be modified:
- `packages/doc-sync/src/folio_sync/indexer.py`
- `packages/doc-sync/src/folio_sync/handler.py`
- `packages/doc-sync/src/folio_sync/s3_client.py`

## 3. Design
### 3.1. Translation Strategy
- Use US English for all docstrings and comments.
- Maintain the original meaning and technical context.
- Follow the PEP 257 docstring conventions already in use.

### 3.2. Mapping
| File | Original (PT) | Translated (EN) |
|---|---|---|
| `indexer.py` | `"""Orquestra core (puro) + DB (shell) para indexação."""` | `"""Orchestrates core (pure) + DB (shell) for indexing."""` |
| `indexer.py` | `"""Indexa um documento. Retorna True se houve mudança."""` | `"""Indexes a document. Returns True if there was a change."""` |
| `indexer.py` | `"""Sincroniza tudo do bucket S3. Retorna stats."""` | `"""Synchronizes everything from the S3 bucket. Returns stats."""` |
| `handler.py` | `"""Lambda handler e CLI para doc-sync."""` | `"""Lambda handler and CLI for doc-sync."""` |
| `handler.py` | `"""Extrai records S3 do envelope Lambda/SQS/SNS (duas camadas de JSON)."""` | `"""Extracts S3 records from the Lambda/SQS/SNS envelope (two JSON layers)."""` |
| `handler.py` | `"""Entry point para Lambda (triggered por SQS)."""` | `"""Entry point for Lambda (triggered by SQS)."""` |
| `handler.py` | `"""Entry point CLI (full sync)."""` | `"""CLI entry point (full sync)."""` |
| `s3_client.py` | `"""S3 client. Imperative shell — todo I/O aqui."""` | `"""S3 client. Imperative shell — all I/O here."""` |

## 4. Verification Plan
- Run existing tests to ensure no regressions: `uv run pytest packages/doc-sync/tests/`
- Manual inspection of the files to ensure all translations are correct and no PT text remains.
