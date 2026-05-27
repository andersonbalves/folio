"""Tests for folio_sync/core/indexer.py — pure document preparation."""

from folio_sync.core.indexer import prepare_document

_RAW = "---\ntitle: Pods\ntags:\n  - concept\n---\n# Pods\n\nPods are the smallest units."


def test_prepare_document_returns_expected_fields():
    doc = prepare_document("content/en/docs/concepts/pods.md", _RAW)

    assert doc["path"] == "content/en/docs/concepts/pods.md"
    assert doc["title"] == "Pods"
    assert doc["content"] == "# Pods\n\nPods are the smallest units."
    assert len(doc["content_hash"]) == 64  # SHA-256 hex
    assert doc["slug"] == "pods"
    assert doc["category"] == "concept"
    assert "units" in doc["description"]
    assert doc["sort_order"] == 0
    assert doc["metadata"] == '{"tags": ["concept"]}'


def test_prepare_document_no_front_matter():
    doc = prepare_document("random/note.md", "# Note\n\nSome text.")
    assert doc["title"] == "Note"
    assert doc["category"] == "general"
    assert doc["metadata"] == '{"tags": []}'


def test_prepare_document_hash_changes_with_content():
    doc1 = prepare_document("p.md", "content A")
    doc2 = prepare_document("p.md", "content B")
    assert doc1["content_hash"] != doc2["content_hash"]
