# App Layer Testing

App functions orchestrate domain and infra. Test them as integration tests: let domain logic run naturally, mock infra only at the external boundary, and assert on observable outcomes (rows inserted, results returned, errors propagated).

## Integration vs Unit

App tests live in `tests/integration/`. They are heavier than unit tests and may require a running DB, but they validate that the layers compose correctly. The app layer is where bugs from incorrect wiring surface.

## Fixture Composition

Compose fixtures rather than nesting setup logic inside test bodies:

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
async def clean_db(test_engine):
    yield test_engine
    async with AsyncSession(test_engine) as session:
        await session.execute(text("DELETE FROM chunks"))
        await session.execute(text("DELETE FROM documents"))
        await session.commit()


@pytest.fixture
def mock_embedder():
    with patch("platform_ingestion.app.pipeline.OllamaClient") as mock_cls:
        instance = mock_cls.return_value
        instance.embed_batch = AsyncMock(
            side_effect=lambda texts: [[0.1] * 1024 for _ in texts]
        )
        yield instance
```

Apply fixtures via `@pytest.mark.usefixtures` when you need setup but do not reference the fixture value directly:

```python
@pytest.mark.asyncio
@pytest.mark.usefixtures("mock_embedder")
async def test_run_ingestion_inserts_documents(tmp_path: Path, clean_db):
    (tmp_path / "doc.md").write_text(
        "---\nid: doc-1\ntitle: Test\nkind: guide\n"
        "language: java\nstatus: active\nowner: team\nlast_reviewed: 2024-01-01\n---\nContent here"
    )

    stats = await run_ingestion(content_dir=tmp_path, engine=clean_db)

    assert stats.inserted == 1
    assert stats.failed == 0
```

## Testing Failure Propagation

App functions should propagate infra failures cleanly. Test that a failure in one step halts the pipeline and returns an appropriate result — not that it silently continues or swallows the error.

```python
@pytest.mark.asyncio
async def test_run_ingestion_embedder_failure_records_error(
    tmp_path: Path, clean_db
):
    (tmp_path / "doc.md").write_text(
        "---\nid: doc-1\ntitle: Test\nkind: guide\n"
        "language: java\nstatus: active\nowner: team\nlast_reviewed: 2024-01-01\n---\nContent"
    )

    with patch("platform_ingestion.app.pipeline.OllamaClient") as mock_cls:
        instance = mock_cls.return_value
        instance.embed_batch = AsyncMock(side_effect=ConnectionError("Ollama down"))

        stats = await run_ingestion(content_dir=tmp_path, engine=clean_db)

    assert stats.failed == 1
    assert stats.inserted == 0
```

## Lifespan Context Managers

For server-based app tests (MCP, agent), use the server's lifespan context manager to start and stop resources cleanly:

```python
@pytest_asyncio.fixture(autouse=True)
async def server_ready(test_engine):
    async with lifespan(app, engine=test_engine):
        yield


@pytest.mark.asyncio
async def test_search_docs_returns_results():
    results = await search_docs(query="how to configure Spring beans", limit=3)

    assert len(results) > 0
    assert all(hasattr(r, "chunk") for r in results)
```

`autouse=True` applies the fixture to every test in the file without explicit declaration. Use it only when every test in the file truly requires server startup.

## Performance Assertions

Integration tests may assert latency or recall targets. Keep thresholds conservative to avoid flakiness from environment noise:

```python
import time


@pytest.mark.asyncio
async def test_search_docs_responds_within_threshold():
    start = time.perf_counter()
    await search_docs(query="Spring configuration", limit=5)
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0, f"Search took {elapsed:.2f}s, expected < 2.0s"
```

## What NOT to Mock in App Tests

Do not mock domain functions — they are pure and fast, and skipping them removes coverage of real behavior. Do not mock your own infra functions — app tests exist specifically to verify that domain and infra compose correctly. Mock only the outermost external systems (Ollama API, external HTTP services, external DBs not under test).

## Organizing Integration Tests

One file per major app workflow:

```
tests/integration/
├── conftest.py          # shared: DB engine, lifespan fixture, known-query fixtures
├── test_ingestion.py    # run_ingestion scenarios
├── test_search.py       # MCP search tool scenarios
└── test_eval.py         # evaluation pipeline scenarios
```

Put the `test_engine` and `clean_db` fixtures in the root `conftest.py` so they are available to all integration test files without duplication.
