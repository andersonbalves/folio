## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-09-06 - [SQL Injection and Container Privilege Escalation]
**Vulnerability:** SQL Injection in DDL strings using f-strings for `embedder.dimensions` in `db.py`, and missing non-root user configuration in Dockerfiles.
**Learning:** In DDL statements like CREATE VIRTUAL TABLE where query parameterization doesn't work, dynamic variables injected in strings must be strictly cast. Docker containers without an explicit non-root `USER` run as root by default, leaving them vulnerable to privilege escalation.
**Prevention:** Explicitly cast variables injected into f-strings (e.g. `int()`) and apply inline directives `# nosec B608` and `# nosemgrep`. Ensure Dockerfiles include `RUN useradd -m appuser && chown -R appuser /app` and `USER appuser`.
