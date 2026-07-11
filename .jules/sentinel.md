## 2025-05-18 - Prevented Info Leakage via Chat Interface Exceptions
**Vulnerability:** The web chat application directly cast exceptions to strings and sent them to the Chainlit frontend UI when a connection to the MCP server failed or an MCP tool encountered an error.
**Learning:** Returning full error traces to the web frontend could potentially leak sensitive environment variables (e.g., `MCP_LAMBDA_URL`, AWS credentials, tokens) and inner workings of the tools (internal paths, backend details, stack traces).
**Prevention:** Exception details should be logged server-side (using Python's `logging` module), and only generic failure messages should be returned to end users.
