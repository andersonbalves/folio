"""Tests for the markdown splitter. Pure — no I/O, no mocks."""

from folio_core.splitter import split_document

_SIMPLE = "# Title\n\nFirst paragraph.\n\nSecond paragraph."

_WITH_SECTIONS = """\
# Root

Intro text.

## Section A

Content of A.

## Section B

Content of B.
"""

_WITH_FENCED_CODE = """\
## Usage

Example:

```python
def hello():
    pass
```

More text after.
"""

_DEEPLY_NESTED = """\
# Chapter

## Part One

### Sub-section

Deep content here.
"""


def test_empty_returns_no_chunks():
    assert split_document("") == []
    assert split_document("   \n  ") == []


def test_simple_doc_produces_chunk():
    chunks = split_document(_SIMPLE)
    assert len(chunks) >= 1
    assert all(c.text for c in chunks)


def test_chunks_indexed_sequentially():
    chunks = split_document(_WITH_SECTIONS)
    for i, c in enumerate(chunks):
        assert c.index == i


def test_heading_path_captured():
    chunks = split_document(_WITH_SECTIONS)
    paths = [c.heading_path for c in chunks]
    assert any("Section A" in p for p in paths)
    assert any("Section B" in p for p in paths)


def test_nested_heading_path_includes_parents():
    chunks = split_document(_DEEPLY_NESTED)
    deep = next(c for c in chunks if "Sub-section" in c.heading_path)
    assert "Chapter" in deep.heading_path
    assert "Part One" in deep.heading_path
    assert "Sub-section" in deep.heading_path


def test_fenced_code_block_not_split():
    chunks = split_document(_WITH_FENCED_CODE, preferred_size=10, max_size=50)
    code_chunk = next((c for c in chunks if "```python" in c.text or "def hello" in c.text), None)
    assert code_chunk is not None
    assert "def hello" in code_chunk.text
    assert "```" in code_chunk.text


def test_chunk_size_respected():
    long_section = "## Big\n\n" + " ".join(["word"] * 200)
    chunks = split_document(long_section, preferred_size=100, max_size=200)
    for c in chunks:
        assert len(c.text) <= 200, f"Chunk exceeds max_size: {len(c.text)}"


def test_small_doc_stays_single_chunk():
    doc = "## Title\n\nShort content."
    chunks = split_document(doc, preferred_size=512, max_size=1024)
    assert len(chunks) == 1
    assert "Short content." in chunks[0].text


def test_section_split_preserves_all_content():
    chunks = split_document(_WITH_SECTIONS)
    combined = " ".join(c.text for c in chunks)
    assert "Content of A" in combined
    assert "Content of B" in combined
    assert "Intro text" in combined


def test_tilde_fence_not_split():
    doc = "## Sec\n\n~~~bash\necho hi\n~~~\n\nAfter."
    chunks = split_document(doc, preferred_size=10, max_size=50)
    fence_chunk = next((c for c in chunks if "echo hi" in c.text), None)
    assert fence_chunk is not None
    assert "~~~" in fence_chunk.text
