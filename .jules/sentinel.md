## 2024-06-08 - Prevented Stack Trace Leak in Chat Application
**Vulnerability:** The Chat Application (`app.py`) was leaking full python stack traces to users on general exceptions using `traceback.format_exc()`.
**Learning:** The fallback error handling logic in the top-level chat loop leaked internal application errors because it was using raw tracebacks to debug instead of standard server-side logging.
**Prevention:** Use a standard logger, like `structlog`, and log `exc_info=True`. Return a generic message to the client, without exposing execution flow or internal states.
