## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-08-31 - [Container Security: Root User and Image Optimization]
**Vulnerability:** Dockerfiles running processes as the root user.
**Learning:** Adding a non-root user and changing ownership of files mitigates container breakout risks. However, running `chown -R` after copying files creates a duplicate Docker layer, bloating the image.
**Prevention:** Always set up the user first and use `COPY --chown=user:user` to optimize layer size while maintaining security.
