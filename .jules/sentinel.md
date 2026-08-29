## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-08-29 - [Missing User in Dockerfiles]
**Vulnerability:** Running Docker containers as root without a non-root USER configured
**Learning:** Dockerfiles (e.g. for doc-sync and mcp-server) should configure a non-root user and properly assign file ownership before the final CMD layer to enforce security best practices.
**Prevention:** Use groupadd, useradd, chown -R and USER folio in Dockerfile.
