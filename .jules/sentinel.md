## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-06-22 - [Error Message Information Disclosure]
**Vulnerability:** The MCP tool execution and connection handlers in the Chainlit web chat interface (`packages/chat/src/folio_chat/shell/app.py`) were returning internal exception details directly to the user.
**Learning:** Exposing internal error messages via the UI can leak sensitive infrastructure details, logic errors, or component versions to end users.
**Prevention:** Catch exceptions and display generic, user-friendly error messages while logging the actual exception and stack trace securely on the server-side using the `logging` module.
