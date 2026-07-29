## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-06-04 - [Run Docker as non-root]
**Vulnerability:** Dockerfiles for doc-sync and mcp-server were running containers as root.
**Learning:** Running containers as root poses a security risk. If a container is compromised, the attacker has root access.
**Prevention:** Always create a non-root user in Dockerfiles and switch to it using the USER command.
