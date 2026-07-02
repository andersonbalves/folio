## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` and `on_chat_start` exception handlers in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
