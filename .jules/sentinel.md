## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-09-02 - [Container Privilege Escalation Risk & SAST False Positives]
**Vulnerability:** Dockerfiles for `doc-sync` and `mcp-server` were running as root, creating a container privilege escalation risk. SAST tools (Semgrep, Bandit) were flagging false-positive SQL injection risks on non-user controlled DDL formatting (like virtual table declarations).
**Learning:** SQLite cannot parameterize DDL queries (like `CREATE VIRTUAL TABLE`), requiring string interpolation for schema creation (e.g. `embedder.dimensions`). This pattern triggers SAST tools even if the variable isn't user-supplied. Similarly, string concatenation used with placeholder generation triggers false positives, despite the query arguments being safely passed in a separate execution tuple.
**Prevention:** Always declare a non-root user (`USER appuser`) in Dockerfiles. When inline variable interpolation or formatting is strictly necessary in SQL queries and demonstrably safe, always append explicit linter suppressions (e.g., `# nosec B608 # nosemgrep`).
