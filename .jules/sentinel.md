## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-07-20 - [Error Message Information Disclosure]
**Vulnerability:** The `on_chat_start` and `_handle_message` exception handlers in the Chainlit web chat interface were returning stringified errors directly to the user.
**Learning:** Returning exception strings via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the exception securely on the server-side using the logging module.
