---
name: python-functional
description: >
  Guia de boas práticas para código Python seguindo o paradigma funcional. /
  Best practices guide for Python code following the functional paradigm.
  Use esta skill sempre que escrever código Python novo, revisar código existente,
  ou quando o usuário mencionar funções puras, imutabilidade, side effects, Result types,
  Railway-oriented programming, observabilidade, async/sync, tipagem moderada, kwargs,
  ou docstrings. Aplique mesmo que o usuário não use esses termos explicitamente.
  Use this skill whenever writing new Python code, reviewing existing code,
  or when the user mentions pure functions, immutability, side effects, Result types,
  Railway-oriented programming, observability, async/sync, moderate typing, kwargs,
  or docstrings — even if they do not use those terms explicitly.
---

# Python Functional — Best Practices

## Philosophy

Functional Python is not forced Haskell. It means preferring functions over classes,
immutable data over mutable state, explicit transformations over side effects, and
errors as values over exceptions as control flow.

The goal is code that is predictable (same inputs → same outputs), testable (no global
state mocks required), and traceable (structured observability).

---

## Reference Index

Before generating or reviewing code, read the reference for the relevant domain:

| Topic | File |
|-------|------|
| Pure functions, immutability, idempotency, side effects | `references/purity-immutability.md` |
| Error handling, Result types, Railway | `references/error-handling.md` |
| Logging, observability, trace_id | `references/observability.md` |
| Typing, kwargs, docstrings, generators, pattern matching | `references/style-guide.md` |
| Async vs sync, concurrency, blocking calls | `references/async-sync.md` |

If the task spans multiple domains, read all relevant references before starting.

---

## Principles at a Glance

### Prefer

- **Pure functions**: same input → same output, nothing external modified
- **Immutable data**: `@dataclass(frozen=True)`, `NamedTuple`, never mutate parameters
- **Errors as values**: return `Result[T, E]` for expected failures; exceptions only for truly exceptional situations
- **Explicit kwargs**: avoid positional arguments when there are more than 2 parameters
- **Contract docstrings**: document what the function guarantees, not how it works
- **Structured logging**: named events with fields, never interpolated strings
- **Async where there is I/O**: do not block the event loop; do not add async without reason

### Avoid

- Unnecessary classes — use functions + data; class only when there are real invariants to protect
- Mutable state at module level — no global variables that change at runtime
- Exceptions as control flow — `try/except` for expected errors signals a design problem
- `print` in production — use structlog with structured fields
- Excessive typing — `x: int = 3` in internal code is noise; type hints matter at boundaries
- Comments explaining *what* — if code needs a comment to be understood, rename or refactor

### Python 3.14 Evolution

- **Multi-Interpreter Parallelism (PEP 734)**: for CPU-bound tasks, prefer the `interpreters` module over `multiprocessing` to leverage per-interpreter GIL and true multicore parallelism.
- **Template Strings (PEP 750)**: use tagged strings for safe DSL and SQL construction.

---

## Mode: Code Generation

When generating new Python code:

1. Read the references for the domains the task touches
2. Structure as a transformation pipeline: `data in → transformation → data out`
3. Isolate side effects (DB, HTTP, FS) in adapter functions called from the top of the call stack
4. For expected failures (e.g., record not found, validation failed), use `Result`
5. Add docstrings to the function contract, not the implementation details
6. Include structured logging at entry and exit points of adapters

**Example structure:**

```python
# Adapter (isolated side effect)
async def fetch_user(user_id: str, *, db: AsyncSession) -> Result["User", str]:
    ...

# Pure transformation (no I/O)
def apply_discount(user: User, *, discount_pct: float) -> User:
    ...

# Orchestrator (composes adapters and transformations)
async def process_user_discount(
    user_id: str, *, discount_pct: float, db: AsyncSession
) -> Result["User", str]:
    return (
        await fetch_user(user_id, db=db)
    ).bind(lambda u: Success(apply_discount(u, discount_pct=discount_pct)))
```

---

## Mode: Code Review

When reviewing existing code, evaluate each point below and flag problems with
a suggested refactoring:

- [ ] Do functions modify their parameters or external state?
- [ ] Are exceptions used for expected control flow?
- [ ] Are classes created just to group functions (no real state)?
- [ ] Are positional arguments used where kwargs would make the call clearer?
- [ ] Is logging done with `print` or f-strings instead of structlog?
- [ ] Does async code block the event loop with synchronous calls?
- [ ] Are type hints missing on public functions or at system boundaries?
- [ ] Do comments explain what the code does instead of why?
- [ ] Is there mutable state at module level?

For each problem found: cite the location, explain the risk, show the functional alternative.

---

## Quick Decisions

**When to use a class:**
A class makes sense when there are invariants that must be maintained across calls
(e.g., stateful connection, progressive builder). For data, prefer `@dataclass(frozen=True)`.

**When to use exception vs Result:**
Use exception for failures the caller cannot anticipate or handle (bug, OOM, disk full).
Use `Result` for expected failures the caller must decide how to handle (not found, validation).

**When to add a type hint:**
On public function signatures, at boundaries with external systems (Pydantic), and when
the type is not obvious from the name. Not on trivial local variables.

**When to use async:**
When there is I/O (network, disk, DB). Not for CPU-bound work. Not by default.
