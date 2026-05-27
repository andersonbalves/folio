from folio_sync.core.categorizer import (
    infer_category,
    infer_description,
    infer_slug,
    infer_sort_order,
    infer_title,
)


def test_infer_category_concepts():
    assert infer_category("content/en/docs/concepts/workloads/pods.md") == "concept"


def test_infer_category_tasks():
    assert infer_category("content/en/docs/tasks/run-application.md") == "task"


def test_infer_category_unknown():
    assert infer_category("random/path/doc.md") == "general"


def test_infer_category_adrs():
    assert infer_category("docs/adrs/001-use-postgres.md") == "adr"


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


def test_infer_description_from_body():
    assert infer_description({}, "# Heading\n\nFirst paragraph.") == "First paragraph."


def test_infer_sort_order_from_weight():
    assert infer_sort_order("p.md", {"weight": 42}) == 42


def test_infer_sort_order_default():
    assert infer_sort_order("p.md", {}) == 0
