from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from folio_sync.config import settings

_pool: AsyncConnectionPool | None = None


async def get_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        conninfo = (
            f"host={settings.database.host} "
            f"port={settings.database.port} "
            f"dbname={settings.database.name} "
            f"user={settings.database.user} "
            f"password={settings.database.password}"
        )
        _pool = AsyncConnectionPool(
            conninfo,
            min_size=settings.database.pool_min_size,
            max_size=settings.database.pool_max_size,
            kwargs={"options": f"-c statement_timeout={settings.database.statement_timeout_ms}"},
        )
        await _pool.open()
    return _pool


@asynccontextmanager
async def conn() -> AsyncIterator[AsyncConnection]:
    pool = await get_pool()
    async with pool.connection() as connection:
        yield connection


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
