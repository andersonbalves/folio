"""Content hashing. Pure, without I/O."""

import hashlib


def content_hash(raw: str) -> str:
    """SHA-256 of the raw content."""
    return hashlib.sha256(raw.encode()).hexdigest()
