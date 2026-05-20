from folio_core.categorizer import (
    infer_category,
    infer_description,
    infer_slug,
    infer_sort_order,
    infer_title,
)


def test_infer_category_concepts():
    # Act
    cat = infer_category("content/en/docs/concepts/workloads/pods.md")
    # Assert
    assert cat == "concept"


def test_infer_category_tasks():
    # Act
    cat = infer_category("content/en/docs/tasks/run-application.md")
    # Assert
    assert cat == "task"


def test_infer_category_unknown():
    # Act
    cat = infer_category("random/path/doc.md")
    # Assert
    assert cat == "general"


def test_infer_slug_with_fm():
    # Act
    slug = infer_slug("path/doc.md", {"topic_slug": "custom-slug"})
    # Assert
    assert slug == "custom-slug"


def test_infer_slug_without_fm():
    # Act
    slug = infer_slug("path/doc.md", {})
    # Assert
    assert slug == "doc"


def test_infer_title_with_fm():
    # Act
    title = infer_title("path/doc.md", {"title": "FM Title"}, "# H1 Title")
    # Assert
    assert title == "FM Title"


def test_infer_title_with_h1():
    # Act
    title = infer_title("path/doc.md", {}, "# H1 Title\nbody text")
    # Assert
    assert title == "H1 Title"


def test_infer_title_fallback_path():
    # Act
    title = infer_title("path/my_custom-doc.md", {}, "body text")
    # Assert
    assert title == "My Custom Doc"


def test_infer_description_with_fm():
    # Act
    desc = infer_description({"description": "FM desc"}, "body text")
    # Assert
    assert desc == "FM desc"


def test_infer_description_from_body():
    # Act
    desc = infer_description({}, "# Title\n\nFirst paragraph\n\nSecond")
    # Assert
    assert desc == "First paragraph"


def test_infer_description_skips_code_blocks():
    # Act
    desc = infer_description({}, "```bash\ncode\n```\nReal paragraph")
    # Assert
    assert desc == "Real paragraph"


def test_infer_sort_order_with_valid_weight():
    # Act
    order = infer_sort_order("path.md", {"weight": 10})
    # Assert
    assert order == 10


def test_infer_sort_order_with_invalid_weight():
    # Act
    order = infer_sort_order("path.md", {"weight": "abc"})
    # Assert
    assert order == 0


def test_infer_sort_order_without_weight():
    # Act
    order = infer_sort_order("path.md", {})
    # Assert
    assert order == 0
