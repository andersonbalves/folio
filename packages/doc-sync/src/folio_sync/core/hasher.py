"""SHA-256 content hashing utilities. Pure, without I/O."""

import hashlib


def content_hash(raw: str) -> str:
    """Return the SHA-256 hex digest of the given raw string content."""
    return hashlib.sha256(raw.encode()).hexdigest()
