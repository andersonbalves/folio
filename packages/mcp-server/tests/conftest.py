"""Shared fixtures for mcp-server tests."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_cursor():
    cursor = AsyncMock()
    cursor.__aenter__ = AsyncMock(return_value=cursor)
    cursor.__aexit__ = AsyncMock(return_value=False)
    return cursor


@pytest.fixture
def mock_conn(mock_cursor):
    connection = AsyncMock()
    connection.__aenter__ = AsyncMock(return_value=connection)
    connection.__aexit__ = AsyncMock(return_value=False)
    connection.cursor = MagicMock(return_value=mock_cursor)
    return connection


@pytest.fixture
def mock_conn_ctx(mock_conn):
    @asynccontextmanager
    async def _conn():
        yield mock_conn

    return _conn
