import hashlib

from folio_core.hasher import content_hash


def test_content_hash():
    # Arrange
    content = "hello world"
    expected = hashlib.sha256(content.encode()).hexdigest()
    # Act
    h = content_hash(content)
    # Assert
    assert h == expected
