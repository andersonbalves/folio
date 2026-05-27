#!/usr/bin/env python
"""Upload seed markdown files from infra/seed/kubernetes-docs to the LocalStack S3 bucket."""

from pathlib import Path

import boto3


def main():
    """Upload all .md files under infra/seed/kubernetes-docs to the folio-docs S3 bucket."""
    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:4566",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    bucket = "folio-docs"
    base_dir = Path("infra/seed/kubernetes-docs")

    if not base_dir.exists():
        return

    for file_path in base_dir.rglob("*.md"):
        relative_path = file_path.relative_to(base_dir)
        key = str(relative_path)
        s3.upload_file(str(file_path), bucket, key)


if __name__ == "__main__":
    main()
