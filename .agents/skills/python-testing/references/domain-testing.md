# Domain Layer Testing

Domain functions are pure: same inputs always produce the same outputs, no I/O, no side effects. This makes them the simplest layer to test — no mocks, no async, no fixtures.

## The Golden Rule

If your domain test needs a mock, the function under test is not pure. Move the I/O dependency to infra and pass the result as a parameter instead.

## Basic Pattern

```python
from platform_ingestion.domain.chunker import chunk_document
from platform_commons.models import Document, DocumentMetadata, ChunkConfig
from datetime import date


def make_document(content: str = "default content") -> Document:
    return Document(
        metadata=DocumentMetadata(
            id="test-doc",
            kind="guide",
            title="Test",
            language="java",
            status="active",
            owner="team",
            last_reviewed=date.today(),
        ),
        content=content,
    )


def test_chunk_document_returns_at_least_one_chunk():
    doc = make_document(content="Hello world. This is a test paragraph.")
    config = ChunkConfig(max_tokens=100, min_tokens=1, max_chars=500)

    chunks = chunk_document(doc, config=config)

    assert len(chunks) >= 1


def test_chunk_document_empty_content_returns_empty_list():
    doc = make_document(content="")
    config = ChunkConfig(max_tokens=100, min_tokens=1, max_chars=500)

    chunks = chunk_document(doc, config=config)

    assert chunks == []
```

## Data Builders

Create `make_<model>()` helper functions at the top of each test file (or in `conftest.py` when shared). Set sensible defaults; let tests override only what matters for that scenario.

```python
def make_chunk(
    content: str = "sample chunk content",
    document_id: str = "doc-1",
    index: int = 0,
) -> Chunk:
    return Chunk(
        id=f"{document_id}-{index}",
        content=content,
        metadata=ChunkMetadata(document_id=document_id, index=index),
    )
```

Builders keep tests short and focused. When a model adds a required field, you update the builder in one place.

## Parametrize for Boundary Values

Use `@pytest.mark.parametrize` to test boundary conditions without duplicating test logic:

```python
import pytest


@pytest.mark.parametrize("content,expected_count", [
    ("", 0),
    ("single paragraph", 1),
    ("para one\n\npara two", 2),
    ("word " * 500, 3),  # forces split on max_tokens
])
def test_chunk_document_count(content: str, expected_count: int):
    doc = make_document(content=content)
    config = ChunkConfig(max_tokens=100, min_tokens=1, max_chars=300)

    chunks = chunk_document(doc, config=config)

    assert len(chunks) == expected_count
```

Always include: below boundary, at boundary, above boundary. The at-boundary case kills the most mutants.

## Result Types

If domain functions return `Result` (from the `returns` library), test both `Success` and `Failure` paths. Testing only the happy path leaves failure branches invisible to mutation testing.

```python
from returns.result import Success, Failure


def test_parse_frontmatter_valid_returns_success():
    raw = "---\nid: doc-1\ntitle: Test\nkind: guide\n---\nContent here"

    result = parse_frontmatter(raw)

    assert isinstance(result, Success), f"Expected Success, got {result}"
    metadata = result.unwrap()
    assert metadata.id == "doc-1"


def test_parse_frontmatter_missing_required_field_returns_failure():
    raw = "---\ntitle: No ID here\n---\nContent"

    result = parse_frontmatter(raw)

    assert isinstance(result, Failure)
```

Always assert `isinstance(result, Success)` before calling `.unwrap()`. An unwrap on `Failure` raises an exception that reads as a test error, not a failure — hiding the real problem.

## Frozen Dataclass Inputs

Domain functions take frozen dataclasses or Pydantic `frozen=True` models. Never mutate inputs in tests. If a scenario requires a variant, create a new instance.

```python
# Wrong — raises AttributeError on frozen model
config = ChunkConfig(max_tokens=100)
config.max_tokens = 200

# Correct — create a new instance
config_larger = ChunkConfig(
    max_tokens=200,
    min_tokens=config.min_tokens,
    max_chars=config.max_chars,
)
```

## What NOT to Test in Domain

- Internal helper functions called only by other domain functions — test the public interface, not the implementation details
- That Pydantic raises `ValidationError` for invalid inputs — Pydantic handles that; your job is testing what your code does with valid inputs
- Type correctness — that is what `ty check` is for
