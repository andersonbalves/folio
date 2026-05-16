# Error Handling — Railway-Oriented Programming

## Philosophy

Exceptions are for truly exceptional situations: programming bugs, infrastructure
failures the caller cannot anticipate or handle. For everything predictable — record
not found, validation failed, quota exceeded — the error is part of the function's
contract and should be returned as a value.

Using `try/except` for normal flow obscures reasoning about code: a reader cannot
know, when calling a function, what errors it might raise without reading the entire
implementation. `Result[T, E]` makes the error visible in the signature.

---

## Library: `returns`

```bash
uv add returns
```

### Core Types

```python
from returns.result import Result, Success, Failure
from returns.maybe import Maybe, Some, Nothing
```

**`Result[T, E]`**: represents either a success (`Success[T]`) or a failure (`Failure[E]`).

**`Maybe[T]`**: represents either a present value (`Some[T]`) or absence (`Nothing`).
Use when absence is not an error, just a normal possibility.

---

## Usage Patterns

### Return Result Instead of Raising

```python
from returns.result import Result, Success, Failure


def parse_positive_int(value: str) -> Result[int, str]:
    try:
        n = int(value)
    except ValueError:
        return Failure(f"'{value}' is not a valid integer")
    if n <= 0:
        return Failure(f"expected positive integer, got {n}")
    return Success(n)
```

### Chaining with `.bind()` and `.map()`

`.map()` transforms the inner value if `Success`, passes `Failure` through unchanged.
`.bind()` chains functions that also return `Result`.

```python
def fetch_user(user_id: str) -> Result[User, str]:
    ...


def check_active(user: User) -> Result[User, str]:
    if not user.active:
        return Failure(f"user {user.id} is inactive")
    return Success(user)


def send_welcome_email(user: User) -> Result[None, str]:
    ...


# Pipeline: failure at any step short-circuits the chain
result: Result[None, str] = (
    fetch_user(user_id)
    .bind(check_active)
    .bind(send_welcome_email)
)
```

### `@safe` Decorator

Automatically converts exceptions into `Failure`:

```python
from returns.result import safe


@safe
def read_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)

# Returns Result[dict, Exception] — never raises
config = read_config("/etc/app/config.json")
```

### Maybe for Optional Absence

```python
from returns.maybe import Maybe


def find_user(user_id: str, *, users: dict[str, User]) -> Maybe[User]:
    user = users.get(user_id)
    return Maybe.from_optional(user)


# Usage
greeting = (
    find_user("u123", users=db)
    .map(lambda u: f"Hello, {u.name}")
    .value_or("User not found")
)
```

---

## When to Use Exception vs Result

| Situation | Approach |
|-----------|----------|
| Record not found | `Failure("not found")` |
| Input validation failed | `Failure("field X is invalid")` |
| Network timeout (expected) | `Failure("timeout after 5s")` |
| Programming bug (assertion) | `raise AssertionError` or `raise RuntimeError` |
| OOM, disk full | let propagate — there is nothing meaningful to "handle" |
| Exception from external library | capture at the boundary with `@safe`, convert to `Failure` |

### Capturing External Library Exceptions at the Boundary

```python
from returns.result import safe
import httpx


@safe(exceptions=(httpx.HTTPError, httpx.TimeoutException))
async def get_resource(url: str, *, client: httpx.AsyncClient) -> dict:
    response = await client.get(url)
    response.raise_for_status()
    return response.json()
```

---

## Unwrapping Results

```python
result = parse_positive_int("42")

# Pattern matching (Python 3.10+) — preferred
match result:
    case Success(value):
        print(f"ok: {value}")
    case Failure(error):
        print(f"error: {error}")

# Alternative: value_or for simple cases
n = result.value_or(0)

# Alternative: unwrap (raises if Failure — use only in tests or when Failure is impossible)
n = result.unwrap()
```

---

## Async with Result

`returns` has native async support:

```python
from returns.future import FutureResult, future_safe


@future_safe
async def fetch_data(url: str, *, client: httpx.AsyncClient) -> dict:
    response = await client.get(url)
    response.raise_for_status()
    return response.json()


async def pipeline() -> FutureResult[str, Exception]:
    return await (
        fetch_data("https://api.example.com/data", client=client)
        .bind_async(transform_data)
        .map(format_output)
    )
```

For projects not yet using `FutureResult`, the simpler approach is to use `Result`
normally in async functions — Python does not prevent this:

```python
async def fetch_user(user_id: str, *, db: AsyncSession) -> Result[User, str]:
    row = await db.get(UserRow, user_id)
    if row is None:
        return Failure(f"user {user_id} not found")
    return Success(User.from_row(row))
```

---

## Preserving Error Context

When chaining operations, preserve context in `Failure` values:

```python
# Bad — loses context about where the error originated
return Failure("not found")

# Good — identifies what was not found and where
return Failure(f"user {user_id!r} not found in fetch_user")
```

For larger systems, consider a structured error type:

```python
@dataclass(frozen=True)
class AppError:
    code: str
    message: str
    context: dict[str, str] = field(default_factory=dict)


def fetch_user(user_id: str) -> Result[User, AppError]:
    ...
    return Failure(AppError(
        code="USER_NOT_FOUND",
        message=f"user {user_id} not found",
        context={"user_id": user_id},
    ))
```
