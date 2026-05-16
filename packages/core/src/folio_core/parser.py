"""Markdown parsing with YAML front matter. Pure, without I/O."""

import yaml

from folio_core.models import ParsedMarkdown


def parse_markdown(raw: str) -> ParsedMarkdown:
    """Separates YAML front matter from the markdown body.

    Handles: no front matter, malformed YAML, empty file.
    """
    if not raw or not raw.startswith("---\n"):
        return ParsedMarkdown(front_matter={}, body=raw or "")
    try:
        _, fm_yaml, body = raw.split("---\n", 2)
        fm = yaml.safe_load(fm_yaml) or {}
        return ParsedMarkdown(front_matter=fm, body=body.lstrip())
    except ValueError, yaml.YAMLError:
        return ParsedMarkdown(front_matter={}, body=raw)
