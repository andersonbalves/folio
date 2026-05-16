"""Lambda handler and CLI for doc-sync."""

import asyncio
import json

import structlog

from folio_sync.db import close_pool
from folio_sync.indexer import full_sync, upsert_document
from folio_sync.s3_client import get_text

logger = structlog.get_logger()


def extract_s3_records(event: dict) -> list[dict]:
    """Extracts S3 records from the Lambda/SQS/SNS envelope (two JSON layers)."""
    records = []
    for sqs_record in event.get("Records", []):
        body = json.loads(sqs_record["body"])
        inner = json.loads(body["Message"]) if "Message" in body else body
        for s3_record in inner.get("Records", []):
            if s3_record.get("eventSource") == "aws:s3":
                records.append(s3_record)
    return records


async def _handle_event(event: dict) -> dict:
    results = {"processed": 0, "errors": 0}
    for record in extract_s3_records(event):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        if not key.endswith(".md"):
            continue
        try:
            content = await get_text(bucket, key)
            await upsert_document(key, content)
            results["processed"] += 1
        except Exception as e:
            logger.exception("sync.record_error", key=key, error=str(e))
            results["errors"] += 1
    await close_pool()
    return results


def lambda_handler(event: dict, context=None) -> dict:
    """Entry point for Lambda (triggered by SQS)."""
    result = asyncio.get_event_loop().run_until_complete(_handle_event(event))
    return {"statusCode": 200, "body": result}


async def _full_sync_cli() -> None:
    await full_sync()
    await close_pool()


def main() -> None:
    """CLI entry point (full sync)."""
    asyncio.run(_full_sync_cli())
