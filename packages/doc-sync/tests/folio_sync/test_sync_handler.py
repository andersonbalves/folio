"""Tests for folio_sync/handler.py — extract_s3_records and _handle_event."""

import json
from unittest.mock import AsyncMock, patch

from folio_sync.handler import _handle_event, extract_s3_records


def _make_event(bucket: str, key: str) -> dict:
    """Build a minimal SQS→SNS→S3 event envelope."""
    s3_event = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {"bucket": {"name": bucket}, "object": {"key": key}},
            }
        ]
    }
    sns_body = {"Message": json.dumps(s3_event)}
    return {"Records": [{"body": json.dumps(sns_body)}]}


# --- extract_s3_records ---


def test_extract_s3_records_sqs_sns_s3():
    event = _make_event("my-bucket", "test.md")
    records = extract_s3_records(event)
    assert len(records) == 1
    assert records[0]["s3"]["bucket"]["name"] == "my-bucket"
    assert records[0]["s3"]["object"]["key"] == "test.md"


def test_extract_s3_records_sqs_s3_direct():
    s3_event = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {"bucket": {"name": "my-bucket"}, "object": {"key": "test2.md"}},
            }
        ]
    }
    sqs_event = {"Records": [{"body": json.dumps(s3_event)}]}
    records = extract_s3_records(sqs_event)
    assert len(records) == 1
    assert records[0]["s3"]["object"]["key"] == "test2.md"


def test_extract_s3_records_empty():
    assert extract_s3_records({}) == []
    assert extract_s3_records({"Records": []}) == []


# --- _handle_event ---


async def test_handle_event_processes_md_file():
    event = _make_event("my-bucket", "docs/pods.md")
    with (
        patch("folio_sync.handler.get_text", AsyncMock(return_value="# Pods")),
        patch("folio_sync.handler.upsert_document", AsyncMock()),
        patch("folio_sync.handler.close_pool", AsyncMock()),
    ):
        result = await _handle_event(event)
    assert result == {"processed": 1, "errors": 0}


async def test_handle_event_skips_non_md_file():
    event = _make_event("my-bucket", "image.png")
    with (
        patch("folio_sync.handler.get_text", AsyncMock()) as mock_get,
        patch("folio_sync.handler.upsert_document", AsyncMock()),
        patch("folio_sync.handler.close_pool", AsyncMock()),
    ):
        result = await _handle_event(event)
    mock_get.assert_not_called()
    assert result == {"processed": 0, "errors": 0}


async def test_handle_event_counts_errors_and_continues():
    """Error on first record must not stop processing of the second record."""
    s3_event = {
        "Records": [
            {"eventSource": "aws:s3", "s3": {"bucket": {"name": "b"}, "object": {"key": "a.md"}}},
            {"eventSource": "aws:s3", "s3": {"bucket": {"name": "b"}, "object": {"key": "c.md"}}},
        ]
    }
    event = {"Records": [{"body": json.dumps({"Message": json.dumps(s3_event)})}]}
    with (
        patch(
            "folio_sync.handler.get_text",
            AsyncMock(side_effect=[RuntimeError("S3 timeout"), "# C"]),
        ),
        patch("folio_sync.handler.upsert_document", AsyncMock()),
        patch("folio_sync.handler.close_pool", AsyncMock()),
    ):
        result = await _handle_event(event)
    assert result == {"processed": 1, "errors": 1}


async def test_handle_event_empty_event():
    with patch("folio_sync.handler.close_pool", AsyncMock()):
        result = await _handle_event({})
    assert result == {"processed": 0, "errors": 0}
