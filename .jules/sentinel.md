## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2024-05-18 - Dockerfile Security Pattern: Non-Root User with Ownership
**Vulnerability:** Dockerfiles running as root by default.
**Learning:** Adding a non-root user is insufficient if the application requires write access to its working directory. `chown -R` must be applied to directories the app user needs to interact with.
**Prevention:** Always follow the pattern `RUN useradd -m appuser && chown -R appuser:appuser /app` and `USER appuser` in Dockerfiles before the final `CMD`.
