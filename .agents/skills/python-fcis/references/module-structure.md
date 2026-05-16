# Module Structure — FCIS

## Layout for a Medium Feature/Service

```
src/feature/
├── domain.py      # Pydantic frozen models — pure domain types
├── core.py        # Pure functions — business logic
└── adapters.py    # I/O — database, HTTP, filesystem
```

No subdirectories until the code grows. When `core.py` exceeds ~200 lines,
promote to a subdirectory.

## Layout for a Larger Service

```
src/
├── core/
│   ├── domain.py     # Pydantic models (frozen=True)
│   ├── logic.py      # Transformations and decisions
│   └── rules.py      # Business validations
├── shell/
│   ├── db.py         # Database adapters
│   ├── http.py       # External HTTP clients
│   └── events.py     # Event publishing
└── services.py       # Orchestration: shell→core→shell
```

## What Goes in Each File

### domain.py
Immutable types shared by the core and the shell. They are the common language.

```python
from datetime import date
from pydantic import BaseModel, ConfigDict

class Order(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    total: float
    status: str

class Discount(BaseModel):
    model_config = ConfigDict(frozen=True)
    code: str
    pct: float
    expires_at: date
```

### core.py / logic.py
Pure functions that take domain types and return domain types.
No I/O imports. Time and IDs received as parameters.

```python
from datetime import date
from .domain import Order, Discount

def apply_discount(order: Order, *, discount: Discount, today: date) -> Order:
    if today > discount.expires_at:
        return order
    return order.model_copy(update={"total": order.total * (1 - discount.pct)})
```

### adapters.py / db.py / http.py
Async functions that perform I/O and return domain types (or Result).
No business logic here.

```python
from returns.result import Result, Success, Failure
from sqlalchemy.ext.asyncio import AsyncSession
from .domain import Order

async def load_order(order_id: str, *, db: AsyncSession) -> Result[Order, str]:
    row = await db.get(OrderRow, order_id)
    if row is None:
        return Failure(f"order {order_id!r} not found")
    return Success(Order.model_validate(row.__dict__))

async def save_order(order: Order, *, db: AsyncSession) -> None:
    await db.merge(OrderRow(**order.model_dump()))
```

### services.py
Wires adapters and core together. It stitches, it does not decide.

```python
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from returns.result import Result, Success, Failure
from .core import apply_discount
from .domain import Order
from .adapters import load_order, save_order, load_discount

async def process_discount(
    order_id: str,
    *,
    discount_code: str,
    db: AsyncSession,
) -> Result[Order, str]:
    today = date.today()  # current time lives here in the shell, never in the core
    discount_result = await load_discount(discount_code, db=db)
    order_result = await load_order(order_id, db=db)

    match (order_result, discount_result):
        case (Success(order), Success(discount)):
            updated = apply_discount(order, discount=discount, today=today)
            await save_order(updated, db=db)
            return Success(updated)
        case (Failure() as f, _) | (_, Failure() as f):
            return f
```

## Import Rules

```
domain.py   →  (nothing from within the project)
core.py     →  domain.py
adapters.py →  domain.py + external I/O libraries
services.py →  core.py + adapters.py + domain.py
handlers.py →  services.py + adapters.py
```

If you add an import that goes in the opposite direction (core importing adapters),
that is a FCIS violation.
