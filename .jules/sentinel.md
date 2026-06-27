## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2024-10-24 - Secure Error Handling in Chainlit App
**Vulnerability:** Information Exposure (CWE-209). The Chainlit frontend `app.py` was returning raw exception strings (`str(e)`) to users when failing to connect to the MCP server or execute tools.
**Learning:** This codebase needs strict enforcement of secure error handling. Exceptions, especially those stemming from external tool calls or network operations (like MCP connections), can inadvertently leak sensitive system details, stack traces, or even credentials if passed directly to the UI.
**Prevention:** Always log the full exception server-side (using `logging.getLogger(__name__).exception(...)` or `structlog`) and return a generic, safe error message to the client.
