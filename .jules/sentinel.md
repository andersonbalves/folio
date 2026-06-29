## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-06-29 - [Exception Details Information Disclosure]
**Vulnerability:** The MCP tool execution handler was returning full exception strings to the user via the UI/CLI.
**Learning:** Returning exception strings exposes sensitive internal context, such as internal error details or stack components.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
