## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2024-05-24 - Secure Error Handling in Chat Interfaces
**Vulnerability:** Internal system exception traces and details were leaked directly to users in error messages within the chat application.
**Learning:** Returning raw exception strings directly to the end user via client-side UI exposes sensitive details about internal architecture, which contradicts the codebase's secure error handling policy.
**Prevention:** Catch generic exceptions, log the full exception trace on the server-side, and return a sanitized, generic error message (e.g., "An internal error occurred. Please try again later.") to the user.
