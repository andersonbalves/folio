"""Tests for indexer.py — upsert_document and full_sync logic."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from folio_sync.indexer import full_sync, upsert_document

_RAW = "---\ntitle: Pods\ntags:\n  - concept\n---\n# Pods\n\nPods are units."
_HASH = "abc123"


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


async def test_upsert_document_indexes_new_doc(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = None  # no existing hash

    with (
        patch("folio_sync.indexer.conn", mock_conn_ctx),
        patch("folio_sync.indexer.content_hash", return_value=_HASH),
    ):
        changed = await upsert_document("concepts/pods.md", _RAW)

    assert changed is True
    assert mock_cursor.execute.call_count == 3  # hash check + doc upsert + topic upsert


async def test_upsert_document_skips_unchanged_doc(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = (_HASH,)  # same hash already in DB

    with (
        patch("folio_sync.indexer.conn", mock_conn_ctx),
        patch("folio_sync.indexer.content_hash", return_value=_HASH),
    ):
        changed = await upsert_document("concepts/pods.md", _RAW)

    assert changed is False
    assert mock_cursor.execute.call_count == 1  # only hash check


async def test_upsert_document_updates_changed_doc(mock_conn_ctx, mock_cursor):
    mock_cursor.fetchone.return_value = ("old_hash",)  # different hash

    with (
        patch("folio_sync.indexer.conn", mock_conn_ctx),
        patch("folio_sync.indexer.content_hash", return_value=_HASH),
    ):
        changed = await upsert_document("concepts/pods.md", _RAW)

    assert changed is True


async def test_full_sync_reports_stats():
    docs = [
        ("concepts/pods.md", _RAW),
        ("concepts/services.md", "# Services"),
    ]

    async def _iter_markdowns(bucket, prefix):
        for key, content in docs:
            yield key, content

    with (
        patch("folio_sync.indexer.iter_markdowns", _iter_markdowns),
        patch("folio_sync.indexer.upsert_document", AsyncMock(side_effect=[True, False])),
    ):
        stats = await full_sync()

    assert stats["scanned"] == 2
    assert stats["indexed"] == 1
    assert stats["skipped"] == 1
