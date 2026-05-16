# Style Guide — Typing, Kwargs, Docstrings, Generators, Pattern Matching

## Moderate Typing

Type hints in Python are a means, not an end. The goal is to communicate intent and
catch errors early — not to annotate every local variable.

### Where to Add Type Hints

**Always:** public function signatures and any boundary with external systems.

```python
# Public boundary — full typing
def calculate_discount(price: float, *, discount_pct: float) -> float:
    ...

# Pydantic at API, DB, or serialization boundaries
class OrderRequest(BaseModel):
    user_id: str
    items: list[OrderItemRequest]
    coupon_code: str | None = None
```

**Rarely necessary:** local variables whose type is obvious from context.

```python
# Unnecessary — the type is obvious
total: float = 0.0
items: list[str] = []

# Useful — the type is not obvious without the annotation
result: Result[User, AppError] = fetch_user(user_id)
```

### Useful Types

```python
from typing import Iterator, Generator, Callable, TypeVar
from collections.abc import Sequence, Iterable, Mapping

T = TypeVar("T")
E = TypeVar("E")

# Accept any iterable, not just lists
def process(items: Iterable[str]) -> Iterator[str]:
    ...

# Callables with a specific signature
Predicate = Callable[[str], bool]
```

### `Protocol` for Abstractions

Avoid inheritance to define contracts. Use `Protocol` (structural duck typing):

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class Repository(Protocol):
    async def get(self, id: str) -> User | None: ...
    async def save(self, user: User) -> None: ...
```

Any class implementing those methods satisfies the protocol — no inheritance required.

---

## Keyword Arguments (Kwargs)

### Enforce Kwargs with `*`

When a function has more than 2 parameters beyond self/the first, force kwargs to make
call sites self-documenting:

```python
# Ambiguous — what does each True mean?
create_user("Alice", "alice@example.com", True, False)

# Clear — intent is explicit
create_user("Alice", email="alice@example.com", active=True, admin=False)

# Enforce kwargs in the signature (caller cannot use positional after *)
def create_user(name: str, *, email: str, active: bool = True, admin: bool = False) -> User:
    ...
```

### When Positional Is Fine

One or two arguments that naturally make sense positionally are acceptable:

```python
# Fine — the subject is obvious positionally
def double(n: float) -> float:
    return n * 2

# Fine — two naturally ordered args
def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))
```

---

## Docstrings

### Contract, Not Implementation

The docstring documents the function's *contract*: what it guarantees, its
preconditions, what can fail. It does not describe *how* it is implemented — that
changes, and the code already shows it.

```python
def transfer_funds(
    amount: Decimal,
    *,
    from_account: str,
    to_account: str,
    idempotency_key: str,
) -> Result[Transaction, TransferError]:
    """Transfer funds between accounts in an idempotent way.

    Repeated calls with the same idempotency_key return the original
    transaction without reprocessing.

    Args:
        amount: Amount to transfer. Must be positive.
        from_account: ID of the source account.
        to_account: ID of the destination account.
        idempotency_key: Unique key per transfer attempt.

    Returns:
        Success with the created Transaction, or Failure with:
        - TransferError.INSUFFICIENT_FUNDS if balance is insufficient
        - TransferError.ACCOUNT_NOT_FOUND if either account does not exist
        - TransferError.SAME_ACCOUNT if from_account == to_account
    """
```

### When to Skip the Docstring

Simple internal functions whose name already says everything:

```python
def _is_weekend(date: date) -> bool:
    return date.weekday() >= 5
```

### Code Comments

Use comments only when the *why* is non-obvious — a hidden constraint, a workaround
for a specific bug, an invariant that would surprise the reader.
Never explain what the code does — the code already does that.

```python
# No: explains the obvious
total = price * quantity  # multiply price by quantity

# Yes: explains the non-obvious why
# Qdrant requires dense vectors to have exactly 1024 dimensions;
# padding is necessary when the model returns fewer dims for short inputs.
vector = pad_to_dim(embedding, target_dim=1024)
```

---

## Generators and Lazy Evaluation

Prefer generators over lists when processing is sequential and volume may be large.
Generators are lazy — they compute one item at a time without materializing everything
in memory.

```python
# List — materializes everything (bad for large volumes)
def active_users(users: list[User]) -> list[User]:
    return [u for u in users if u.active]


# Generator — lazy
def active_users(users: Iterable[User]) -> Iterator[User]:
    return (u for u in users if u.active)


# Generator function with yield
def chunk_list(items: list[T], *, size: int) -> Iterator[list[T]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]
```

### Generator Pipelines

Chain generators for efficient pipelines:

```python
def process_records(path: str) -> Iterator[OutputRecord]:
    raw = read_lines(path)              # Iterator[str]
    parsed = parse_records(raw)         # Iterator[RawRecord]
    valid = filter(is_valid, parsed)    # Iterator[RawRecord]
    return map(transform, valid)        # Iterator[OutputRecord]
```

Each stage processes one item at a time — without loading the entire file into memory.

---

## Pattern Matching

`match`/`case` (Python 3.10+) is more expressive than `if/elif` chains when
discriminating over data structure.

### Discriminating over Result

```python
match result:
    case Success(user):
        logger.info("user_found", user_id=user.id)
        return user
    case Failure(error):
        logger.warning("user_not_found", error=error)
        raise HTTPException(status_code=404, detail=error)
```

### Discriminating over Type or Structure

```python
match event:
    case {"type": "order_created", "order_id": str(order_id)}:
        await handle_order_created(order_id)
    case {"type": "payment_received", "amount": float(amount)}:
        await handle_payment(amount)
    case {"type": unknown_type}:
        logger.warning("unknown_event_type", event_type=unknown_type)
```

### When to Prefer If/Elif

For simple conditions without structural discrimination, `if/elif` is clearer:

```python
# Don't force match where if is more readable
if value > 100:
    ...
elif value > 50:
    ...
else:
    ...
```

---

## Functions vs Classes

Use a class when there are **invariants that must be protected** across calls —
that is, when internal state cannot be constructed arbitrarily.

```python
# Class justified: ConnectionPool maintains the invariant that max_connections is never exceeded
class ConnectionPool:
    def __init__(self, *, max_connections: int) -> None:
        ...


# Class unnecessary: just groups static functions
class MathUtils:
    @staticmethod
    def double(n: float) -> float:
        return n * 2
    # → simply: def double(n: float) -> float: return n * 2
```

For data with simple behavior, `@dataclass(frozen=True)` with methods is preferable
to a class with a manual `__init__`.
