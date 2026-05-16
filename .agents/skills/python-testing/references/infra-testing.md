# Infra Layer Testing

Infra functions perform I/O: read files, call APIs, query databases. Test them by replacing the external system with a controlled substitute at the boundary — not deep inside your own code.

## The Boundary Rule

Mock the outermost layer you do not own: the filesystem driver, the HTTP client class, the DB connection factory. Never mock a function you wrote inside your own infra layer — if it touches the system, test it with a real substitute (`tmp_path`, a test DB, an HTTP mock server) or mock the external library class itself.

## Filesystem: Use tmp_path

pytest's `tmp_path` fixture provides a real temporary directory. Prefer it over mocking `open` or `Path`:

```python
import pytest
from pathlib import Path
from returns.result import Success, Failure
from platform_ingestion.infra.loader import load_documents


@pytest.mark.asyncio
async def test_load_documents_valid_frontmatter(tmp_path: Path):
    # Arrange
    (tmp_path / "doc.md").write_text(
        "---\nid: doc-1\ntitle: Test\nkind: guide\n"
        "language: java\nstatus: active\nowner: team\nlast_reviewed: 2024-01-01\n---\nContent"
    )

    # Act
    result = await load_documents(tmp_path)

    # Assert
    assert isinstance(result, Success)
    docs = result.unwrap()
    assert len(docs) == 1
    assert docs[0].metadata.id == "doc-1"


@pytest.mark.asyncio
async def test_load_documents_empty_directory_returns_empty(tmp_path: Path):
    result = await load_documents(tmp_path)

    assert isinstance(result, Success)
    assert result.unwrap() == []


@pytest.mark.asyncio
async def test_load_documents_malformed_frontmatter_returns_failure(tmp_path: Path):
    (tmp_path / "bad.md").write_text("no frontmatter here, just text")

    result = await load_documents(tmp_path)

    assert isinstance(result, Failure)
```

`tmp_path` is automatically cleaned up after each test. No teardown needed.

## HTTP / LLM APIs: Use AsyncMock

```python
from unittest.mock import AsyncMock, patch
from returns.result import Success, Failure
from platform_ingestion.infra.embedder import embed_chunks


@pytest.mark.asyncio
async def test_embed_chunks_returns_embeddings():
    chunks = [make_chunk(content="hello"), make_chunk(content="world")]

    with patch("platform_ingestion.infra.embedder.OllamaClient") as mock_cls:
        instance = mock_cls.return_value
        instance.embed_batch = AsyncMock(
            return_value=[[0.1] * 1024, [0.2] * 1024]
        )

        result = await embed_chunks(chunks, client=instance)

    assert isinstance(result, Success)
    embedded = result.unwrap()
    assert len(embedded) == 2
    assert len(embedded[0].embedding) == 1024


@pytest.mark.asyncio
async def test_embed_chunks_api_error_returns_failure():
    chunks = [make_chunk()]

    with patch("platform_ingestion.infra.embedder.OllamaClient") as mock_cls:
        instance = mock_cls.return_value
        instance.embed_batch = AsyncMock(side_effect=ConnectionError("API down"))

        result = await embed_chunks(chunks, client=instance)

    assert isinstance(result, Failure)
```

**Patch at the import site.** Patch `platform_ingestion.infra.embedder.OllamaClient`, not `platform_commons.llm.OllamaClient`. Python resolves the name where it is imported, not where it is defined.

## Database: Fixture with Cleanup

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def clean_session(test_engine):
    async with AsyncSession(test_engine) as session:
        yield session
        await session.execute(text("DELETE FROM chunks"))
        await session.execute(text("DELETE FROM documents"))
        await session.commit()


@pytest.mark.asyncio
async def test_index_chunks_inserts_rows(clean_session: AsyncSession):
    chunks = [make_embedded_chunk()]

    result = await index_chunks(chunks, session=clean_session)

    assert isinstance(result, Success)
    count = await clean_session.scalar(text("SELECT COUNT(*) FROM chunks"))
    assert count == 1
```

Clean up **after** the test in the fixture's teardown (after `yield`), not before. pytest runs fixture teardown even on test failure, guaranteeing isolation without relying on prior state.

## Async Fixture Declaration

Use `@pytest_asyncio.fixture` for async fixtures (not `@pytest.fixture`):

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def connected_client():
    client = MyAsyncClient()
    await client.connect()
    yield client
    await client.disconnect()
```

## What to Test per Infra Function

For every infra function, write at minimum:

1. **Happy path**: valid input → `Success` with expected data shape
2. **Failure path**: system error (connection failure, missing file, malformed response) → `Failure`
3. **Edge case**: empty input, zero results, boundary size

Do not test every possible error message. Test that the right type is returned (`Failure`) and that the failure carries actionable information.
