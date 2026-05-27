"""Tests for folio_sync/shell/handler.py — CLI entry point."""

from unittest.mock import AsyncMock, patch

from folio_sync.shell.handler import main


def test_main_runs_full_sync():
    with (
        patch(
            "folio_sync.shell.handler.full_sync",
            AsyncMock(return_value={"scanned": 0, "indexed": 0, "skipped": 0}),
        ),
        patch("folio_sync.shell.handler.close_pool", AsyncMock()),
    ):
        main()
