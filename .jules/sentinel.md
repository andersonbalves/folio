## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2026-08-26 - [SQL Injection and Missing USER]
**Vulnerability:** Found unparameterized string formatting in SQLite DDL queries and root user execution in Dockerfiles.
**Learning:** SQLite DDL statements do not support prepared parameters, leading to false positives or real string injection risks when formatted dynamically. Containers without a specified non-root USER inherently risk running as root.
**Prevention:** explicitly cast dynamically injected values in DDL (like `int()`) and use scanner suppression comments (`# nosec B608`, `# nosemgrep`). Ensure every Dockerfile creates and switches to a dedicated user.
