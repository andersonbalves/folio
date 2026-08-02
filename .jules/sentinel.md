## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2026-06-04 - [Error Message Information Disclosure in Chainlit Tools/Connection]
**Vulnerability:** The MCP tool execution and MCP connection initialization exception handlers in `packages/chat/src/folio_chat/shell/app.py` were returning full stack traces directly to the user interface via stringification of exceptions (`str(e)`).
**Learning:** Returning exception details through the Chainlit UI, especially for background tasks or generic tool calls, can inadvertently expose internal directory structure, potential library versions, server architecture (like Lambda URL details), and execution context to potentially malicious users.
**Prevention:** Always catch generic exceptions and display a user-friendly, non-descriptive error message in the UI, while logging the full stack trace securely on the server-side using the `logging` module.
