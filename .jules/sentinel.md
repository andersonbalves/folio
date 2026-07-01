## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2026-06-04 - [Error Message Information Disclosure Update]
**Vulnerability:** The exceptions in `app.py` when a tool call fails or when the MCP connection fails, and in `chat.py` when a tool call fails were returning the raw exception strings (`str(e)`) to the user.
**Learning:** Returning full stack traces or raw exception strings via the UI or CLI exposes internal directory structure, potential library versions, backend URIs, or token details.
**Prevention:** Catch generic exceptions, log the stack trace securely on the server-side using the `logging` module (`logging.getLogger(__name__).exception(...)`), and display a user-friendly error message without sensitive information.
