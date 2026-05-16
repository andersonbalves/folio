# Async vs Sync — When to Use and How Not to Mix Them

## Fundamental Rule

Use `async` when there is I/O (network, disk, database). Use sync when there is
CPU-bound processing or pure logic. Do not add `async` by default — every `await`
is a coordination point that has a cost and must justify its existence.

---

## When to Use Async

```python
# Correct: network I/O → async
async def fetch_embedding(text: str, *, client: httpx.AsyncClient) -> list[float]:
    response = await client.post("/embed", json={"text": text})
    return response.json()["embedding"]


# Correct: database query → async
async def get_user(user_id: str, *, db: AsyncSession) -> User | None:
    return await db.get(User, user_id)
```

## When to Stay Sync

```python
# Correct: pure transformation → sync
def normalize_vector(vector: list[float]) -> list[float]:
    magnitude = sum(x**2 for x in vector) ** 0.5
    return [x / magnitude for x in vector]


# Correct: CPU-bound parsing/chunking → sync
def chunk_text(text: str, *, size: int, overlap: int) -> list[str]:
    ...
```

---

## The Problem: Blocking Calls Inside Async

Calling blocking code (synchronous I/O) inside an async function freezes the entire
event loop — all running coroutines stop while the blocking call does not return.

```python
# PROBLEM: requests is synchronous — blocks the event loop
async def fetch_data_broken(url: str) -> dict:
    response = requests.get(url)  # blocks! never do this
    return response.json()


# CORRECT: use httpx.AsyncClient or equivalent
async def fetch_data(url: str, *, client: httpx.AsyncClient) -> dict:
    response = await client.get(url)
    return response.json()
```

### Other Common Pitfalls

```python
# PROBLEM: time.sleep inside async
async def poll():
    time.sleep(5)  # blocks the event loop

# CORRECT: asyncio.sleep releases the event loop
async def poll():
    await asyncio.sleep(5)


# PROBLEM: synchronous open() + read() in async functions
async def read_file_broken(path: str) -> str:
    return open(path).read()  # blocks on disk I/O

# CORRECT: aiofiles for file I/O in async context
import aiofiles
async def read_file(path: str) -> str:
    async with aiofiles.open(path) as f:
        return await f.read()
```

---

## Running Blocking Code in Async Context

When you must call a synchronous blocking library from within async code, delegate
to a thread pool via `asyncio.run_in_executor`:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor


# Synchronous CPU-bound function or third-party blocking I/O
def heavy_computation(data: bytes) -> str:
    ...  # uses a synchronous library


async def process(data: bytes) -> str:
    loop = asyncio.get_event_loop()
    # runs in thread pool — does not block the event loop
    return await loop.run_in_executor(None, heavy_computation, data)
```

For heavy CPU-bound work, prefer `ProcessPoolExecutor` over the default
`ThreadPoolExecutor` (which still suffers from the GIL):

```python
from concurrent.futures import ProcessPoolExecutor

executor = ProcessPoolExecutor()

async def cpu_intensive(data: bytes) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, heavy_computation, data)
```

---

## Concurrency: asyncio.gather

To run multiple coroutines in parallel:

```python
import asyncio


# Runs the 3 fetches concurrently
user, orders, settings = await asyncio.gather(
    fetch_user(user_id, db=db),
    fetch_orders(user_id, db=db),
    fetch_settings(user_id, db=db),
)
```

### Error Handling in gather

By default, `gather` cancels everything if any coroutine raises an exception.
Use `return_exceptions=True` to collect errors individually:

```python
results = await asyncio.gather(
    fetch_a(),
    fetch_b(),
    fetch_c(),
    return_exceptions=True,
)

for result in results:
    if isinstance(result, Exception):
        logger.error("fetch_failed", error=str(result))
```

---

## asyncio.TaskGroup (Python 3.11+)

Prefer `TaskGroup` over `gather` when creating tasks dynamically and wanting
clean cancellation semantics:

```python
async def process_batch(items: list[str]) -> list[Result]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(process_item(item)) for item in items]
    # All tasks finished here (or TaskGroup raised ExceptionGroup)
    return [t.result() for t in tasks]
```

---

## asyncio.run — Entrypoints Only

`asyncio.run()` creates a new event loop. Call it only at the top level of the
program (the entrypoint), never inside libraries or functions that may be called
from an existing async context.

```python
# Entrypoint — fine
if __name__ == "__main__":
    asyncio.run(main())


# Library — never
def my_function():
    asyncio.run(coroutine())  # creates nested loop — error in Python 3.10+
```

---

## Async Context Managers

Use `async with` for resources that need asynchronous setup/teardown:

```python
# Database session
async with AsyncSessionMaker() as session:
    user = await session.get(User, user_id)

# HTTP client — reuse across requests
async with httpx.AsyncClient(timeout=10.0) as client:
    data = await fetch_data(url, client=client)
```

### Lifespan for Persistent Resources

In long-running applications (servers, workers), manage resources via lifespan
instead of creating and closing them per request:

```python
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    # Setup: create shared resources
    async with httpx.AsyncClient() as http_client:
        async with AsyncSessionMaker() as db:
            yield {"http_client": http_client, "db": db}
    # Teardown: automatic cleanup on exit
```

---

## Summary

| Situation | Approach |
|-----------|----------|
| Network I/O | `async` + async library (httpx, aiohttp) |
| Database I/O | `async` + async driver (asyncpg, SQLAlchemy async) |
| Disk I/O | `async` + aiofiles |
| CPU-bound | sync, run in `ProcessPoolExecutor` if needed |
| Synchronous blocking lib | `run_in_executor` with `ThreadPoolExecutor` |
| Multiple independent ops | `asyncio.gather` or `TaskGroup` |
| Polling with wait | `asyncio.sleep`, never `time.sleep` |
| Program entrypoint | `asyncio.run(main())` exactly once |
