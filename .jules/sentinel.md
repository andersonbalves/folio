## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2025-02-27 - [Information Leakage in Error Responses]
**Vulnerability:** The MCP server connection (`on_chat_start`) and tool calling exceptions (`_handle_message`) in the `folio_chat` app returned explicit error strings containing internal details directly to the user.
**Learning:** Returning `str(e)` in error messages can leak sensitive internal state, network topology details, or secrets.
**Prevention:** Catch generic exceptions, log them securely on the server using `.exception()`, and return abstract, user-friendly error messages that do not expose application internals.
