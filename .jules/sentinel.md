## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.

## 2026-06-05 - [Error Message Information Disclosure in Chat App]
**Vulnerability:** The exception handlers in `on_chat_start` and `_handle_message` inside the Chainlit web chat interface (`packages/chat/src/folio_chat/shell/app.py`) were returning the raw exception string `str(e)` directly to the user/UI.
**Learning:** Exposing raw exception strings can reveal internal infrastructure details, network topology, or library errors to end users, especially during connection failures or tool call failures.
**Prevention:** Always log exceptions server-side with `logging.getLogger(__name__).exception` and return a generic, user-friendly error message to the client, without exposing the underlying `Exception` details.
