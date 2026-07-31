## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2024-07-31 - [Information Leakage in Web UI Error Messages]
**Vulnerability:** The web chat UI (Chainlit application) exposed full exception messages (`str(e)`) to the client during tool execution and MCP connection failures.
**Learning:** Returning exception details to the client can inadvertently expose sensitive internal paths, environment details, or underlying system states that should be kept private.
**Prevention:** Always catch exceptions, log the full details securely on the server-side, and return a safe, generic error message to the client. This implements the "Fail securely" principle and prevents information disclosure.
