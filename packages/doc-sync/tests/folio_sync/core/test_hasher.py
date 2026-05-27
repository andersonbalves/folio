import hashlib

from folio_sync.core.hasher import content_hash


def test_content_hash():
    content = "hello world"
    expected = hashlib.sha256(content.encode()).hexdigest()
    assert content_hash(content) == expected


def test_content_hash_empty():
    assert content_hash("") == hashlib.sha256(b"").hexdigest()
