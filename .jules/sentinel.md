## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2026-06-04 - [Dockerfile Privilege Escalation & SQL Injection False Positives]
**Vulnerability:** Dockerfiles in `packages/doc-sync` and `packages/mcp-server` were running as root by default. Additionally, Semgrep incorrectly flagged a `CREATE VIRTUAL TABLE USING vec0` command as SQL injection.
**Learning:** Always specify a non-root user in Dockerfiles to prevent container privilege escalation. DDL SQL injection false positives, such as dynamic schema definitions with vector dimensions, need careful handling and exclusion rules when native parameterization isn't possible.
**Prevention:** Add `groupadd` and `useradd` for a non-root user and use the `USER` instruction in all Dockerfiles. For unparameterizable SQL concatenation, enforce input sanitization (e.g., `int()`) and use explicit `# nosemgrep # nosec B608` exclusions.