# Testing — FCIS

## Core: Zero Mocks

Pure functions need no mocks. Tests are input-in, output-out assertions.

```python
# tests/unit/test_core.py
from datetime import date
from decimal import Decimal
from src.feature.core import apply_discount, validate_order
from src.feature.domain import Order, Discount, OrderRequest

def test_discount_not_applied_after_expiry():
    order = Order(id="1", total=100.0, status="open")
    discount = Discount(code="SUMMER", pct=0.10, expires_at=date(2024, 1, 1))
    result = apply_discount(order, discount=discount, today=date(2024, 6, 1))
    assert result.total == 100.0

def test_discount_applied_before_expiry():
    order = Order(id="1", total=100.0, status="open")
    discount = Discount(code="SUMMER", pct=0.10, expires_at=date(2024, 12, 31))
    result = apply_discount(order, discount=discount, today=date(2024, 6, 1))
    assert result.total == 90.0

def test_order_validation_rejects_empty_items():
    req = OrderRequest(id="x", total=50.0, items=[])
    result = validate_order(req)
    assert result.is_failure()
```

No fixtures. No `@pytest.mark.asyncio`. No `patch`. Plain `def`.

Testing time-dependent logic is trivial because time is injected:

```python
def test_discount_valid_today():
    discount = Discount(code="D", pct=0.05, expires_at=date(2024, 6, 15))
    assert is_discount_valid(discount, today=date(2024, 6, 15))

def test_discount_expired_yesterday():
    discount = Discount(code="D", pct=0.05, expires_at=date(2024, 6, 14))
    assert not is_discount_valid(discount, today=date(2024, 6, 15))
```

## Shell: Integration Tests with Real I/O

Shell adapters are tested against real infrastructure (database, HTTP).
In CI without infrastructure, mock only the adapter, never the core logic.

```python
# tests/integration/test_adapters.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.feature.adapters import load_order, save_order
from src.feature.domain import Order

@pytest.mark.asyncio
async def test_save_and_load_roundtrip(db: AsyncSession):
    order = Order(id="roundtrip-1", total=42.0, status="open")
    await save_order(order, db=db)
    result = await load_order("roundtrip-1", db=db)
    assert result.is_success()
    assert result.unwrap().total == 42.0

@pytest.mark.asyncio
async def test_load_order_not_found(db: AsyncSession):
    result = await load_order("nonexistent", db=db)
    assert result.is_failure()
```

## Service: Integration Tests for the Full Slice

Services orchestrate core + adapters. Test a complete use-case slice.

```python
# tests/integration/test_services.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.feature.services import create_and_discount_order
from src.feature.domain import OrderRequest

@pytest.mark.asyncio
async def test_order_created_without_discount(db: AsyncSession):
    req = OrderRequest(id="svc-1", total=100.0, items=["a"])
    result = await create_and_discount_order(req, discount_code=None, db=db)
    assert result.is_success()
    assert result.unwrap().total == 100.0

@pytest.mark.asyncio
async def test_order_total_discounted(db: AsyncSession, seed_discount):
    req = OrderRequest(id="svc-2", total=100.0, items=["a"])
    result = await create_and_discount_order(req, discount_code="SUMMER10", db=db)
    assert result.is_success()
    assert result.unwrap().total == 90.0
```

## When Infrastructure Is Unavailable in CI

If the test database is not available, mock only the adapter boundary —
never mock core logic.

```python
# Acceptable: mocking the shell adapter in isolation
from unittest.mock import AsyncMock, patch
from returns.result import Success

@pytest.mark.asyncio
async def test_service_calls_save_on_success():
    req = OrderRequest(id="x", total=50.0, items=["b"])
    mock_order = Order(id="x", total=50.0, status="open")

    with (
        patch("src.feature.services.load_discount", return_value=Success(None)),
        patch("src.feature.services.save_order", new_callable=AsyncMock) as mock_save,
    ):
        result = await create_and_discount_order(req, discount_code=None, db=None)
        mock_save.assert_called_once()
```

Prefer real integration tests. Mocking the shell is acceptable when infrastructure
is unavailable. Never mock the core — if you feel the urge, the function has I/O
that needs to be extracted first.

## Test Layout Convention

```
tests/
├── unit/           # Core tests — pure, no fixtures, no async
│   └── test_core.py
└── integration/    # Shell and service tests — fixtures, async, real DB
    ├── test_adapters.py
    └── test_services.py
```

The split makes it obvious which tests can run anywhere and which need infrastructure.
