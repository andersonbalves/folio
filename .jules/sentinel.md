## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-06-04 - [Error Message Information Disclosure in tool calls]
**Vulnerability:** The `_handle_message` and `on_chat_start` functions in the Chainlit web chat interface were returning unhandled tool call and connection exceptions to the user (`str(e)`).
**Learning:** Returning unhandled exception strings via the UI can expose sensitive internal details about the MCP server, prompt injection errors, or system topology.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the `logging` module.
