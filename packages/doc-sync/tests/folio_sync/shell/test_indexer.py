"""Tests for folio_sync/shell/indexer.py — DB upsert logic."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from folio_sync.shell.indexer import full_sync, upsert_document

_PREPARED = {
    "path": "concepts/pods.md",
    "content": "# Pods\n\nPods are units.",
    "content_hash": "abc123",
    "title": "Pods",
    "slug": "pods",
    "category": "concept",
    "description": "Pods are units.",
    "sort_order": 0,
    "metadata": '{"tags": []}',
}


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


async def test_upsert_indexes_new_doc(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = None  # no existing hash

    with (
        patch("folio_sync.shell.indexer.conn", mock_conn_ctx),
        patch("folio_sync.shell.indexer.prepare_document", return_value=_PREPARED),
    ):
        changed = await upsert_document("concepts/pods.md", "raw")

    assert changed is True
    assert mock_cursor.execute.call_count == 3  # hash check + doc upsert + topic upsert


async def test_upsert_skips_unchanged_doc(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = ("abc123",)  # hash matches

    with (
        patch("folio_sync.shell.indexer.conn", mock_conn_ctx),
        patch("folio_sync.shell.indexer.prepare_document", return_value=_PREPARED),
    ):
        changed = await upsert_document("concepts/pods.md", "raw")

    assert changed is False
    assert mock_cursor.execute.call_count == 1  # only hash check


async def test_upsert_updates_changed_doc(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = ("old_hash",)  # different hash

    with (
        patch("folio_sync.shell.indexer.conn", mock_conn_ctx),
        patch("folio_sync.shell.indexer.prepare_document", return_value=_PREPARED),
    ):
        changed = await upsert_document("concepts/pods.md", "raw")

    assert changed is True


async def test_full_sync_reports_stats():
    docs = [("concepts/pods.md", "raw1"), ("concepts/services.md", "raw2")]

    async def _iter(bucket, prefix):
        for key, content in docs:
            yield key, content

    with (
        patch("folio_sync.shell.indexer.iter_markdowns", _iter),
        patch("folio_sync.shell.indexer.upsert_document", AsyncMock(side_effect=[True, False])),
    ):
        stats = await full_sync()

    assert stats == {"scanned": 2, "indexed": 1, "skipped": 1}
