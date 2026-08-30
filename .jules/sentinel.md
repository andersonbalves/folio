## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2025-02-27 - [Suppressing SAST warnings in DDL format strings]
**Vulnerability:** A virtual table schema definition dynamically used string formatting for the embedder dimensions because sqlite doesn't allow parametrized execution `?` inside `CREATE VIRTUAL TABLE`. This triggered a SQL Injection warning from Semgrep.
**Learning:** Due to SQLite limitations with `?` in DDL commands, it is sometimes necessary to use string formatting safely. However, standard `# nosemgrep` placement can break the query syntax if placed directly inside the SQL string as SQLite doesn't recognize `#` as a comment. To safely use formatting and ignore false positives, one must ensure variables injected are strictly sanitized (e.g., cast to integers) and that `# nosec` annotations are applied to the Python string, outside the literal query block.
**Prevention:** Avoid formatting in SQL where standard parametrization works. Where DDL requires dynamic properties (like vector dimensions), strictly sanitize inputs (cast to int, validate enums), and use explicit Python query variables so suppression comments (`# nosec B608 # nosemgrep`) can be appended on the assignment line to prevent scanner failures and SQLite syntax errors.
