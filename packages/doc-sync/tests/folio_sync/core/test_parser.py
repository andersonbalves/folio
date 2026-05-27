from folio_sync.core.parser import parse_markdown


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
