from folio_core.parser import parse_markdown


def test_parse_markdown_with_valid_front_matter():
    # Arrange
    content = "---\ntitle: test\n---\n# body"
    # Act
    parsed = parse_markdown(content)
    # Assert
    assert parsed.front_matter == {"title": "test"}
    assert parsed.body == "# body"


def test_parse_markdown_without_front_matter():
    # Arrange
    content = "# Just body\nline 2"
    # Act
    parsed = parse_markdown(content)
    # Assert
    assert parsed.front_matter == {}
    assert parsed.body == "# Just body\nline 2"


def test_parse_markdown_with_invalid_yaml():
    # Arrange
    content = "---\ntitle: : : invalid\n---\n# body"
    # Act
    parsed = parse_markdown(content)
    # Assert
    assert parsed.front_matter == {}
    assert parsed.body == content


def test_parse_markdown_empty_file():
    # Arrange
    content = ""
    # Act
    parsed = parse_markdown(content)
    # Assert
    assert parsed.front_matter == {}
    assert parsed.body == ""


def test_parse_markdown_only_heading():
    # Arrange
    content = "# Heading only"
    # Act
    parsed = parse_markdown(content)
    # Assert
    assert parsed.front_matter == {}
    assert parsed.body == "# Heading only"


def test_parse_markdown_empty_front_matter():
    # Arrange
    content = "---\n---\n# body"
    # Act
    parsed = parse_markdown(content)
    # Assert
    assert parsed.front_matter == {}
    assert parsed.body == "# body"
