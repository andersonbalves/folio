"""Metadata inference from path and front matter. Pure, without I/O.

Designed to work with docs WITHOUT complete front matter (e.g. Kubernetes docs).
"""

from pathlib import Path


def infer_category(path: str) -> str:
    """Infer the topic category from the document path.

    Matches known directory names (starters, adrs, runbooks, etc.).
    Returns "general" when no known directory is found.

    Args:
        path: S3 key or relative file path of the document.
    """
    parts = Path(path).parts
    if "starters" in parts:
        return "starter"
    if "adrs" in parts:
        return "adr"
    if "runbooks" in parts:
        return "runbook"
    if "concepts" in parts:
        return "concept"
    if "tasks" in parts:
        return "task"
    if "tutorials" in parts:
        return "tutorial"
    if "reference" in parts:
        return "reference"
    return "general"


def infer_slug(path: str, front_matter: dict) -> str:
    """Infer the topic slug from front matter or the file stem.

    Args:
        path: Document path.
        front_matter: Parsed YAML front matter.
    """
    if slug := front_matter.get("topic_slug"):
        return slug
    return Path(path).stem


def infer_title(path: str, front_matter: dict, body: str) -> str:
    """Infer the document title from front matter, first H1, or file stem.

    Args:
        path: Document path.
        front_matter: Parsed YAML front matter.
        body: Markdown body text.
    """
    if title := front_matter.get("title"):
        return title
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return Path(path).stem.replace("-", " ").replace("_", " ").title()


def infer_description(front_matter: dict, body: str) -> str:
    """Infer a short description from front matter or the first prose paragraph.

    Skips headings and code blocks. Truncates at 200 characters.

    Args:
        front_matter: Parsed YAML front matter.
        body: Markdown body text.
    """
    if desc := front_matter.get("description"):
        return desc.strip() if isinstance(desc, str) else str(desc).strip()

    in_code_block = False
    for line in body.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        if stripped and not stripped.startswith("#"):
            return stripped[:200]
    return ""


def infer_sort_order(path: str, front_matter: dict) -> int:
    """Infer the sort order from the front matter weight field.

    Returns 0 when the field is absent or non-numeric.

    Args:
        path: Document path (unused, reserved for future path-based ordering).
        front_matter: Parsed YAML front matter.
    """
    if weight := front_matter.get("weight"):
        try:
            return int(weight)
        except ValueError, TypeError:
            pass
    return 0
