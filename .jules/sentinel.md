## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2024-05-18 - [Privileged Container Execution]
**Vulnerability:** The Dockerfiles for `mcp-server` and `doc-sync` were running their processes as the root user by default.
**Learning:** Running applications as root within a container increases the risk and impact of a potential container escape vulnerability.
**Prevention:** Create a non-root user and group, adjust ownership of application directories, and use the `USER` directive to drop privileges before executing the final `CMD`.
