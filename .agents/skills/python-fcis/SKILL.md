---
name: python-fcis
description: >
  Guia arquitetural para implementar Functional Core Imperative Shell (FCIS) em Python. /
  Architectural guide for implementing Functional Core Imperative Shell (FCIS) in Python.
  Use esta skill sempre que estruturar um novo módulo ou feature Python; ao revisar código
  que mistura lógica de negócio com I/O; ao criar pipelines de processamento; ou quando
  o usuário mencionar FCIS, functional core, imperative shell, separação de camadas,
  testabilidade, pure core, adapter pattern, ports and adapters, hexagonal architecture,
  ou qualquer variação de "como separar lógica de I/O em Python".
  Use mesmo que o usuário não mencione FCIS explicitamente — se há funções que misturam
  decisões de domínio com banco/HTTP/filesystem, este skill se aplica.
  Use this skill whenever structuring a new Python module or feature; when reviewing code
  that mixes business logic with I/O; when building processing pipelines; or when the user
  mentions FCIS, functional core, imperative shell, layer separation, testability, pure core,
  adapter pattern, ports and adapters, hexagonal architecture, or any variation of
  "how to separate I/O from logic in Python" — even implicitly.
  Use alongside the python-functional skill for full coverage.
---

# FCIS — Functional Core Imperative Shell

## The Pattern

FCIS divides code into two zones with radically different responsibilities:

**Functional Core** — what the system *decides*
- Pure functions: same input → same output, no I/O
- Contains all business logic and transformations
- Never imports database, HTTP, filesystem, or clock
- Trivially testable without mocks

**Imperative Shell** — what the system *does*
- Orchestrates I/O: database, external APIs, filesystem, current time
- Calls the core with concrete values, applies the results
- Thin by design — minimal logic, maximum wiring
- Tested with integration tests, not unit tests

Dependency arrow always points: **Shell → Core**. The core never imports the shell.

---

## Reference Index

| Topic | File |
|-------|------|
| Module layout and file organization | `references/module-structure.md` |
| Concrete code patterns (core vs shell) | `references/patterns.md` |
| How to test FCIS code | `references/testing.md` |

Read only the reference relevant to the task at hand.

---

## Core Principles

### What belongs in the Core

- Business logic, validations, calculations
- Data transformations (input → output, no I/O)
- Decisions based on values passed as parameters
- Domain types (`@dataclass(frozen=True)` or Pydantic with `model_config = ConfigDict(frozen=True)`)
- Time and randomness received as parameters, never called internally

### What belongs in the Shell

- Database reads and writes
- HTTP calls and external service communication
- Reading environment variables and configuration
- `datetime.now()`, `uuid4()`, `random()`
- Structured logging with structlog (intentional side effect)
- Entry points: FastAPI routes, MCP tools, event handlers

### The Golden Rule

If a file in the core imports `asyncio`, `httpx`, `sqlalchemy`, `boto3`, `os.environ`,
or any I/O library — it belongs in the shell.

---

## Quick Review Checklist

When reviewing code for FCIS compliance:

**In the Core — violation flags:**
- [ ] Imports an I/O library (`httpx`, `sqlalchemy`, `aiofiles`, `boto3`)?
- [ ] Calls `datetime.now()` or `date.today()` directly?
- [ ] Has mutable state at module level?
- [ ] Produces side effects beyond the return value?

**In the Shell — violation flags:**
- [ ] Contains business logic or domain conditionals?
- [ ] Mixes I/O orchestration with data transformation in the same function?
- [ ] Does the core import anything from the shell?

For each violation: cite the location, explain why it breaks FCIS, show the refactoring.

---

## Python 3.14+ Modern Patterns

- **Deferred Annotations (PEP 649/749)**: annotations are now evaluated only when needed (deferred). `from __future__ import annotations` is no longer needed and should be removed.
- **Modern Exception Handling (PEP 758)**: `except*` clauses can now be used even when the exception is not an `ExceptionGroup`, simplifying hybrid orchestration logic.

---

## Dependency Injection

The core receives **concrete values** (not clients, not sessions).
The shell receives clients/sessions and passes concrete values to the core.

```python
# ✓ Core receives data
def calculate_tax(items: list[Item], *, tax_rate: float) -> Decimal: ...

# ✗ Core receives an I/O client
def calculate_tax(items: list[Item], *, db: AsyncSession) -> Decimal: ...
```

Injection happens at the handler/service level:

```python
# handler (shell)
@router.post("/invoice")
async def create_invoice(body: InvoiceRequest, db: AsyncSession = Depends(get_db)):
    items = await fetch_items(body.item_ids, db=db)        # shell: I/O
    total = calculate_tax(items, tax_rate=current_rate())  # core: pure
    await save_invoice(total, db=db)                       # shell: I/O
```

---

## When FCIS Gets Hard

**Iteration with I/O** (e.g., processing an event stream): split into batches —
fetch a batch (shell) → process the batch (core) → persist results (shell).

**Decisions that depend on external state** (e.g., "does this user have permission?"):
fetching the permission is the shell's job; deciding what to do *with* it is the core's.

**Mandatory side effects mid-pipeline** (e.g., publishing an event between steps):
refactor the core to return a list of commands/events that the shell executes at the end —
the core describes what should happen, the shell makes it happen.
