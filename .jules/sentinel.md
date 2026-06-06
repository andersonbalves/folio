## 2026-06-06 - Prevent Stack Trace Leakage
**Vulnerability:** The `on_message` event handler in the Chainlit web app exposed raw Python stack traces to the end user on unhandled exceptions.
**Learning:** This information disclosure vulnerability could allow attackers to understand the internal directory structure and dependencies of the application.
**Prevention:** Catch generic exceptions and display user-friendly error messages while logging the stack trace internally using `logging.error('...', exc_info=True)`.
