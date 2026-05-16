# Purity, Immutability, and Idempotency

## Pure Functions

A pure function has two properties: given the same input, it always produces the same
output (determinism); and it produces no observable side effects (no I/O, no mutation
of external state, no global variables).

Pure functions are trivially testable (no mocks), composable, and parallelizable.

```python
# Pure — testable with no setup
def calculate_tax(amount: float, *, rate: float) -> float:
    return amount * rate


# Impure — depends on external state, not testable in isolation
def calculate_tax_impure(amount: float) -> float:
    return amount * TAX_RATE  # TAX_RATE is a global
```

### Isolating Side Effects

Side effects (I/O, database, system clock, random) are necessary — they just need to
be **isolated**. The pattern is to push them to the edges: the core logic stays pure;
adapter functions do the I/O and pass concrete data to the core.

```python
# Pure core
def enrich_order(order: Order, *, tax_rate: float, current_time: datetime) -> Order:
    return dataclasses.replace(
        order,
        tax=order.subtotal * tax_rate,
        processed_at=current_time,
    )


# Adapter with side effects — calls the core with concrete data
async def process_order(order_id: str, *, db: AsyncSession) -> Result[Order, str]:
    raw = await db.get(OrderRow, order_id)
    if raw is None:
        return Failure(f"order {order_id} not found")
    order = Order.from_row(raw)
    enriched = enrich_order(
        order,
        tax_rate=settings.TAX_RATE,
        current_time=datetime.now(UTC),
    )
    await db.merge(enriched.to_row())
    return Success(enriched)
```

---

## Immutability

### Data as Values

Never modify a parameter. Return a new instance with the changes applied.

```python
@dataclass(frozen=True)
class User:
    id: str
    name: str
    email: str
    active: bool = True


# Correct: returns a new object
def deactivate(user: User) -> User:
    return dataclasses.replace(user, active=False)


# Wrong: mutates the parameter
def deactivate_bad(user: User) -> None:
    user.active = False  # type: ignore — frozen=True raises FrozenInstanceError
```

### Frozen Dataclasses

Use `@dataclass(frozen=True)` for domain structs. This ensures no code accidentally
modifies data after creation.

For collections inside frozen dataclasses, use `tuple` instead of `list`:

```python
@dataclass(frozen=True)
class Order:
    id: str
    items: tuple[OrderItem, ...]  # tuple, not list
    total: Decimal
```

### NamedTuple for Simple Data

For data without behavior, `NamedTuple` is even lighter:

```python
from typing import NamedTuple


class Coordinates(NamedTuple):
    lat: float
    lon: float
```

### Avoid Mutating Received Collections

```python
# Wrong: modifies the received list
def add_item(items: list[str], new_item: str) -> list[str]:
    items.append(new_item)  # side effect: the caller sees the change
    return items


# Correct: returns a new list
def add_item(items: list[str], new_item: str) -> list[str]:
    return [*items, new_item]
```

---

## Idempotency

An idempotent function can be called multiple times with the same input and produce
the same final state. Essential for write operations in distributed systems.

```python
# Idempotent: applying the same coupon twice does not change the second result
async def apply_coupon(
    order_id: str, *, coupon_code: str, db: AsyncSession
) -> Result[Order, str]:
    order = await db.get(Order, order_id)
    if order is None:
        return Failure("order not found")
    if order.coupon_code == coupon_code:
        return Success(order)  # already applied, return without error
    updated = dataclasses.replace(order, coupon_code=coupon_code, discount=...)
    await db.merge(updated)
    return Success(updated)
```

### Upsert Instead of Insert

Write operations should be idempotent by default. Prefer upsert (insert or update)
over blind insert.

---

## Composition

Pure functions compose naturally. Prefer linear pipelines over deep nesting:

```python
# Nested — hard to follow
result = format_output(filter_active(sort_by_date(parse_records(raw_data))))


# Pipeline with intermediate assignments — more readable
records = parse_records(raw_data)
sorted_records = sort_by_date(records)
active_records = filter_active(sorted_records)
output = format_output(active_records)


# Generator pipeline — lazy, efficient for large volumes
def process_pipeline(raw_data: Iterable[dict]) -> Iterator[str]:
    records = (parse_record(r) for r in raw_data)
    active = (r for r in records if r.active)
    return (format_record(r) for r in active)
```

### functools

```python
from functools import partial, reduce

# partial — specialize generic functions
apply_vat = partial(calculate_tax, rate=0.20)
apply_isr = partial(calculate_tax, rate=0.15)

# reduce — accumulate results explicitly
total = reduce(lambda acc, item: acc + item.price, order.items, Decimal(0))
```
