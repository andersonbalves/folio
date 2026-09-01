## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2024-05-24 - Fix SQL injection vulnerability in SQLite DDL
**Vulnerability:** A potential SQL injection vulnerability (or a static analysis false positive) was present in `packages/doc-sync/src/folio_sync/shell/db.py` due to using an f-string to construct a SQL `CREATE VIRTUAL TABLE` query.
**Learning:** Standard SQL parameters cannot be used for structural schema elements. When dynamic variables must be injected into DDL statements, they must be manually sanitized or cast explicitly (e.g., to `int`) before f-string formatting.
**Prevention:** Always manually sanitize or explicitly cast dynamic variables before injecting them into DDL statements. Use linter suppression comments to prevent false positive scanner alerts on safely constructed DDL queries.
