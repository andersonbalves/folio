## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2026-08-27 - [SAST Scanner False Positives in SQLite DDL & F-Strings]
**Vulnerability:** SAST scanners like Bandit incorrectly flag parameterized SQL f-strings (e.g., `WHERE id IN ({placeholders})`) and dynamically formatted SQLite DDL statements (where native parametrization is unsupported) as `B608:hardcoded_sql_expressions` SQL injection vulnerabilities.
**Learning:** These false positives block CI/CD pipelines or clutter security reports despite the code being secure (using explicit type casting or legitimate parameterized placeholders in the f-string).
**Prevention:** For SQLite DDL statements using f-strings, manually sanitize or explicitly cast injected variables (e.g., to `int`). For all safe f-string SQL constructions, append `# nosec B608 # nosemgrep` to the line to explicitly suppress scanner warnings and signal intent to other developers.
