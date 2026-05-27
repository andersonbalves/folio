import hashlib

from folio_sync.core.document import (
    content_hash,
    infer_category,
    infer_description,
    infer_slug,
    infer_sort_order,
    infer_title,
    parse_markdown,
)


def test_infer_category_concepts():
    assert infer_category("content/en/docs/concepts/workloads/pods.md") == "concept"


def test_infer_category_tasks():
    assert infer_category("content/en/docs/tasks/run-application.md") == "task"


def test_infer_category_unknown():
    assert infer_category("random/path/doc.md") == "general"


def test_infer_category_adrs():
    assert infer_category("docs/adrs/001-use-postgres.md") == "adr"


def test_infer_category_starters():
    assert infer_category("docs/starters/001-starter.md") == "starter"


def test_infer_category_runbooks():
    assert infer_category("docs/runbooks/alert.md") == "runbook"


def test_infer_category_tutorials():
    assert infer_category("docs/tutorials/hello.md") == "tutorial"


def test_infer_category_reference():
    assert infer_category("docs/reference/api.md") == "reference"


def test_infer_slug_from_front_matter():
    assert infer_slug("some/path/file.md", {"topic_slug": "my-slug"}) == "my-slug"


def test_infer_slug_from_path():
    assert infer_slug("some/path/my-doc.md", {}) == "my-doc"


def test_infer_title_from_front_matter():
    assert infer_title("p.md", {"title": "My Title"}, "") == "My Title"


def test_infer_title_from_h1():
    assert infer_title("p.md", {}, "# Heading\n\nBody") == "Heading"


def test_infer_title_from_stem():
    assert infer_title("path/my-doc.md", {}, "no heading") == "My Doc"


def test_infer_description_from_front_matter():
    assert infer_description({"description": "My desc"}, "") == "My desc"


def test_infer_description_from_body_in_code_block():
    body = "```python\n# not desc\n```\nActual desc."
    assert infer_description({}, body) == "Actual desc."


def test_infer_description_from_body():
    assert infer_description({}, "# Heading\n\nFirst paragraph.") == "First paragraph."


def test_infer_sort_order_from_weight():
    assert infer_sort_order("p.md", {"weight": 42}) == 42


def test_infer_sort_order_from_weight_invalid():
    assert infer_sort_order("p.md", {"weight": "invalid"}) == 0


def test_infer_sort_order_default():
    assert infer_sort_order("p.md", {}) == 0


def test_content_hash():
    content = "hello world"
    expected = hashlib.sha256(content.encode()).hexdigest()
    assert content_hash(content) == expected


def test_content_hash_empty():
    assert content_hash("") == hashlib.sha256(b"").hexdigest()


def test_parse_markdown_with_valid_front_matter():
    parsed = parse_markdown("---\ntitle: test\n---\n# body")
    assert parsed.front_matter == {"title": "test"}
    assert parsed.body == "# body"


def test_parse_markdown_without_front_matter():
    parsed = parse_markdown("# Just body\nline 2")
    assert parsed.front_matter == {}
    assert parsed.body == "# Just body\nline 2"


def test_parse_markdown_with_invalid_yaml():
    content = "---\ntitle: : : invalid\n---\n# body"
    parsed = parse_markdown(content)
    assert parsed.front_matter == {}
    assert parsed.body == content


def test_parse_markdown_empty_file():
    parsed = parse_markdown("")
    assert parsed.front_matter == {}
    assert parsed.body == ""


def test_parse_markdown_empty_front_matter():
    parsed = parse_markdown("---\n---\n# body")
    assert parsed.front_matter == {}
    assert parsed.body == "# body"
