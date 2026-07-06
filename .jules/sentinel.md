## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2024-05-18 - [Error Message Information Disclosure]
**Vulnerability:** The `on_chat_start` and `_handle_message` exception handlers in the Chainlit web chat interface (`packages/chat/src/folio_chat/shell/app.py`) were returning exception details to the user.
**Learning:** Returning exception details via the UI exposes internal execution context and potentially sensitive environment variables.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the `logging` module.
