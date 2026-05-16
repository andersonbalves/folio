# Code Patterns — FCIS

## Core: Simple Pure Function

```python
# core.py
from datetime import date
from .domain import Order, Discount

def apply_discount(order: Order, *, discount: Discount, today: date) -> Order:
    """Applies discount if not expired. Returns order unchanged if expired."""
    if today > discount.expires_at:
        return order
    new_total = order.total * (1 - discount.pct)
    return order.model_copy(update={"total": new_total})
```

Key points: no external imports, `today` as parameter (not `date.today()`), returns new object.

## Core: Transformation Pipeline

```python
# core.py
from .domain import RawDocument, Chunk

def split_into_chunks(doc: RawDocument, *, max_tokens: int) -> list[Chunk]:
    paragraphs = doc.text.split("\n\n")
    chunks: list[Chunk] = []
    current: list[str] = []
    current_tokens = 0
    for para in paragraphs:
        tokens = estimate_tokens(para)
        if current_tokens + tokens > max_tokens and current:
            chunks.append(Chunk(text="\n\n".join(current), doc_id=doc.id))
            current, current_tokens = [], 0
        current.append(para)
        current_tokens += tokens
    if current:
        chunks.append(Chunk(text="\n\n".join(current), doc_id=doc.id))
    return chunks

def estimate_tokens(text: str) -> int:
    return len(text) // 4
```

## Core: Validation with Result

```python
# core.py
from returns.result import Result, Success, Failure
from .domain import OrderRequest, Order

def validate_order(req: OrderRequest) -> Result[Order, str]:
    if req.total <= 0:
        return Failure("total must be positive")
    if not req.items:
        return Failure("order must have at least one item")
    return Success(Order(id=req.id, total=req.total, items=req.items))
```

## Shell: Database Adapter

```python
# adapters.py
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from returns.result import Result, Success, Failure
from .domain import Order

log = structlog.get_logger()

async def load_order(order_id: str, *, db: AsyncSession) -> Result[Order, str]:
    row = await db.get(OrderRow, order_id)
    if row is None:
        return Failure(f"order {order_id!r} not found")
    order = Order.model_validate(row.__dict__)
    log.debug("order.loaded", order_id=order_id)
    return Success(order)

async def save_order(order: Order, *, db: AsyncSession) -> None:
    await db.merge(OrderRow(**order.model_dump()))
    log.info("order.saved", order_id=order.id)
```

## Shell: HTTP Adapter

```python
# adapters.py
import httpx
from returns.result import Result, Success, Failure
from .domain import ExternalRate

async def fetch_exchange_rate(
    currency: str, *, client: httpx.AsyncClient
) -> Result[ExternalRate, str]:
    try:
        resp = await client.get(f"/rates/{currency}")
        resp.raise_for_status()
        return Success(ExternalRate.model_validate(resp.json()))
    except httpx.HTTPStatusError as e:
        return Failure(f"rate fetch failed: {e.response.status_code}")
```

## Service: Orchestration (Shell → Core → Shell)

```python
# services.py
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from returns.result import Result, Success, Failure
from .core import apply_discount, validate_order
from .domain import Order, OrderRequest
from .adapters import load_order, save_order, load_discount

async def create_and_discount_order(
    req: OrderRequest,
    *,
    discount_code: str | None,
    db: AsyncSession,
) -> Result[Order, str]:
    order_result = validate_order(req)           # core: pure validation
    if order_result.is_failure():
        return order_result

    order = order_result.unwrap()

    if discount_code:
        discount_result = await load_discount(discount_code, db=db)  # shell: I/O
        if discount_result.is_success():
            order = apply_discount(              # core: pure transformation
                order,
                discount=discount_result.unwrap(),
                today=date.today(),              # current time belongs in the shell
            )

    await save_order(order, db=db)              # shell: I/O
    return Success(order)
```

## Entry Point: FastAPI Handler / MCP Tool

```python
# handlers.py
from fastapi import APIRouter, Depends, HTTPException
from returns.result import Success, Failure
from sqlalchemy.ext.asyncio import AsyncSession
from .domain import OrderRequest, Order
from .services import create_and_discount_order
from .db import get_db

router = APIRouter()

@router.post("/orders", response_model=Order)
async def create_order(
    body: OrderRequest,
    discount_code: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await create_and_discount_order(body, discount_code=discount_code, db=db)
    match result:
        case Success(order):
            return order
        case Failure(msg):
            raise HTTPException(status_code=422, detail=msg)
```

---

## Anti-Patterns

### ✗ Core with hidden I/O

```python
# WRONG: database fetch inside a core function
def apply_discount(order_id: str, *, db: AsyncSession) -> Order:
    order = db.get(Order, order_id)  # I/O in the core — FCIS violation
    ...
```

### ✗ Shell with domain logic

```python
# WRONG: business decision inside an adapter
async def save_order(order: Order, *, db: AsyncSession) -> None:
    if order.total > 1000:          # business logic in the shell
        order = apply_vip_discount(order)
    await db.merge(OrderRow(**order.model_dump()))
```

### ✗ Core accessing time or randomness directly

```python
# WRONG — makes the function non-deterministic and untestable
from datetime import date

def is_discount_valid(discount: Discount) -> bool:
    return date.today() <= discount.expires_at

# CORRECT — today is injected, function is pure
def is_discount_valid(discount: Discount, *, today: date) -> bool:
    return today <= discount.expires_at
```
