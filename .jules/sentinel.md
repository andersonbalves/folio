## 2026-06-04 - [Error Message Information Disclosure]
**Vulnerability:** The `on_message` exception handler in the Chainlit web chat interface was returning full stack traces to the user.
**Learning:** Returning full stack traces via the UI exposes internal directory structure, potential library versions, and execution context.
**Prevention:** Catch generic exceptions and display a user-friendly error message, while logging the stack trace securely on the server-side using the logging module.
## 2026-06-04 - [Error Message Information Disclosure in Chainlit]
**Vulnerability:** The exception handling blocks in `packages/chat/src/folio_chat/shell/app.py` and `packages/chat/src/folio_chat/shell/chat.py` were catching generic exceptions and returning the stringified exception (`str(e)`) to the user.
**Learning:** Exposing full stack traces and internal error strings via the UI or CLI exposes internal execution context and sensitive system details, enabling potential adversaries. Furthermore, swallowing exceptions in backend services without logging them reduces observability and makes diagnosing issues extremely difficult.
**Prevention:** Catch generic exceptions and display a user-friendly, non-descriptive error message, while explicitly logging the detailed stack trace on the server-side using the standard `logging.getLogger(__name__).exception` or `structlog`.
