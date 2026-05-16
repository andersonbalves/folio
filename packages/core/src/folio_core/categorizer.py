"""Metadata inference from path and front matter. Pure, without I/O.

Designed to work with docs WITHOUT complete front matter (e.g. Kubernetes docs).
"""

from pathlib import Path


def infer_category(path: str) -> str:
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
    if slug := front_matter.get("topic_slug"):
        return slug
    return Path(path).stem


def infer_title(path: str, front_matter: dict, body: str) -> str:
    if title := front_matter.get("title"):
        return title
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return Path(path).stem.replace("-", " ").replace("_", " ").title()


def infer_description(front_matter: dict, body: str) -> str:
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
    if weight := front_matter.get("weight"):
        try:
            return int(weight)
        except ValueError, TypeError:
            pass
    return 0
