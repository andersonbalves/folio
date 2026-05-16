# Observability — Structured Logging

## Philosophy

Logs are for operators, not developers. A well-written log answers "what happened,
with what data, in what context" without requiring manual code inspection. Interpolated
strings are hard to parse; structured events with fields are indexable, filterable,
and correlatable.

---

## Library: `structlog`

```bash
uv add structlog
```

### Configuration (once, at the entrypoint)

```python
import structlog
import logging


def configure_logging(*, level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper()),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
```

### Getting the Logger

```python
import structlog

logger = structlog.get_logger()
```

Instantiate at module level — `structlog.get_logger()` is lightweight and opens no connections.

---

## Usage Patterns

### Log Events, Not Messages

The first argument is the event name — use snake_case, short noun or verb.
Additional fields provide context.

```python
# Bad — interpolated string, not structured
logger.info(f"User {user_id} logged in from {ip_address}")

# Good — event + fields
logger.info("user_login", user_id=user_id, ip=ip_address)
```

### Context Binding

Use `.bind()` to propagate context throughout an operation without repeating fields:

```python
async def process_order(order_id: str, *, user_id: str) -> Result[Order, str]:
    log = logger.bind(order_id=order_id, user_id=user_id)

    log.info("order_processing_started")
    result = await fetch_order(order_id)

    match result:
        case Success(order):
            log.info("order_fetched", total=str(order.total))
            ...
        case Failure(error):
            log.warning("order_fetch_failed", error=error)
            return result
```

### trace_id — Cross-Service Correlation

In systems with multiple services or HTTP requests, propagate a `trace_id` that allows
correlating all logs for a single operation:

```python
import uuid
import structlog


def bind_trace_id(trace_id: str | None = None) -> str:
    tid = trace_id or str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(trace_id=tid)
    return tid


# At the entrypoint of each request (HTTP middleware, MCP handler, etc.)
async def handle_request(request: Request) -> Response:
    trace_id = request.headers.get("X-Trace-Id")
    bind_trace_id(trace_id)
    ...
```

With `merge_contextvars` in the structlog pipeline, `trace_id` appears automatically
in all logs produced during that request, without needing to pass it manually.

---

## What to Log

### Adapters (I/O boundaries)

Log at the start and end of I/O operations:

```python
async def fetch_user(user_id: str, *, db: AsyncSession) -> Result[User, str]:
    log = logger.bind(user_id=user_id)
    log.debug("db_fetch_started", table="users")

    row = await db.get(UserRow, user_id)

    if row is None:
        log.info("db_fetch_miss", table="users")
        return Failure(f"user {user_id} not found")

    log.debug("db_fetch_hit", table="users")
    return Success(User.from_row(row))
```

### Business Outcomes

Log when business state changes:

```python
log.info("order_completed", order_id=order.id, total=str(order.total), items=len(order.items))
log.warning("payment_declined", order_id=order.id, reason=decline_reason)
log.error("fraud_detected", order_id=order.id, score=fraud_score)
```

### Errors and Exceptions

```python
try:
    result = risky_operation()
except Exception:
    log.exception("unexpected_error", operation="risky_operation")
    raise
```

`log.exception()` captures the traceback automatically.

---

## Log Levels

| Level | When to use |
|-------|-------------|
| `debug` | Diagnostic data, individual DB calls — dev only |
| `info` | Normal business events, start/end of important operations |
| `warning` | Abnormal but recoverable situation (retry, fallback, degradation) |
| `error` | Failure that prevents the operation (but the service keeps running) |
| `exception` | Same as error, but captures and includes the traceback |
| `critical` | Failure that compromises the entire service |

---

## What Not to Log

- **Sensitive data**: passwords, tokens, SSN, card numbers. Mask explicitly.
- **Every line of code** — "entered here" / "passed through here" logs are noise.
- **`print`** — never in production code.

```python
# Masking sensitive data
log.info("user_authenticated", user_id=user_id, token=token[:8] + "...")
```

---

## Metrics vs Logs

Logs answer "what happened". Metrics answer "how many times / how fast".
For metrics, use a dedicated library (Prometheus, OpenTelemetry) — do not try to
infer metrics by parsing logs.

For projects needing distributed tracing, `structlog` integrates with OpenTelemetry
via `opentelemetry-instrumentation`.
