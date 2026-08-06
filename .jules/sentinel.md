## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2026-08-06 - [Container Privilege Escalation Risk]
**Vulnerability:** The Dockerfiles for `doc-sync` and `mcp-server` were running application containers as the `root` user by default.
**Learning:** Running applications as root inside a container violates the principle of least privilege. If an attacker gains code execution, they have root access inside the container, making container escape attacks much easier.
**Prevention:** Always ensure a non-root user (e.g., `appuser`) is created and assigned ownership of necessary application files, and switch to this user using the `USER` directive before the container's final execution layer.
