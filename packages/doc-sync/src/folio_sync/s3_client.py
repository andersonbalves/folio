"""S3 client. Imperative shell — all I/O here."""

import asyncio
from collections.abc import AsyncIterator

import boto3

from folio_sync.config import settings


def _build_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3.endpoint_url,
        region_name=settings.s3.region,
        aws_access_key_id=settings.s3.access_key,
        aws_secret_access_key=settings.s3.secret_key,
    )


async def get_text(bucket: str, key: str) -> str:
    client = _build_client()
    resp = await asyncio.to_thread(client.get_object, Bucket=bucket, Key=key)
    return resp["Body"].read().decode("utf-8")


async def iter_markdowns(bucket: str, prefix: str = "") -> AsyncIterator[tuple[str, str]]:
    client = _build_client()
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".md"):
                content = await get_text(bucket, key)
                yield key, content
