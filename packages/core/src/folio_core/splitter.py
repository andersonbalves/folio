"""Markdown document splitter. Pure, without I/O."""

import re

from folio_core.models import Chunk


def split_document(
    content: str,
    preferred_size: int = 512,
    max_size: int = 1024,
) -> list[Chunk]:
    """Split markdown content into semantic Chunks.

    Splits at H1-H3 heading boundaries first, then by paragraph within each
    section when the section exceeds preferred_size. Never splits inside a
    fenced code block (``` or ~~~).

    Args:
        content: Raw markdown body text (front matter already stripped).
        preferred_size: Target chunk size in characters.
        max_size: Hard upper bound; chunks are never larger than this.
    """
    if not content or not content.strip():
        return []

    sections = _split_into_sections(content)
    results: list[Chunk] = []

    for section_text, heading_path in sections:
        for fragment in _split_section(section_text, preferred_size, max_size):
            results.append(Chunk(text=fragment, index=len(results), heading_path=heading_path))

    return results


def _split_into_sections(content: str) -> list[tuple[str, str]]:
    """Split content at H1-H3 heading boundaries.

    Returns list of (section_text, heading_path) pairs. heading_path is the
    ' > '-joined trail of parent headings, e.g. 'Workloads > Pods'.
    """
    sections: list[tuple[str, str]] = []
    current_lines: list[str] = []
    heading_stack: list[tuple[int, str]] = []
    in_fence = False

    def flush() -> None:
        text = "\n".join(current_lines).strip()
        if text:
            hp = " > ".join(h for _, h in heading_stack)
            sections.append((text, hp))

    for line in content.split("\n"):
        if re.match(r"^(`{3,}|~{3,})", line):
            in_fence = not in_fence
            current_lines.append(line)
            continue

        if in_fence:
            current_lines.append(line)
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.+)", line)
        if heading_match:
            flush()
            current_lines = [line]
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            heading_stack = [(lvl, h) for lvl, h in heading_stack if lvl < level]
            heading_stack.append((level, title))
        else:
            current_lines.append(line)

    flush()
    return sections


def _split_section(text: str, preferred_size: int, max_size: int) -> list[str]:
    """Split a single section by paragraph when it exceeds preferred_size."""
    if len(text) <= preferred_size:
        return [text]

    paragraphs = _split_paragraphs(text)
    chunks: list[str] = []
    pending: list[str] = []
    pending_size = 0

    for para in paragraphs:
        para_size = len(para)

        if para_size > max_size:
            if pending:
                chunks.append("\n\n".join(pending))
                pending = []
                pending_size = 0
            chunks.extend(_hard_split(para, max_size))
            continue

        join_cost = 2 if pending else 0
        if pending_size + join_cost + para_size > preferred_size and pending:
            chunks.append("\n\n".join(pending))
            pending = []
            pending_size = 0

        pending.append(para)
        pending_size += (2 if pending_size else 0) + para_size

    if pending:
        chunks.append("\n\n".join(pending))

    return chunks or [text]


def _split_paragraphs(text: str) -> list[str]:
    """Split text at blank lines, respecting fenced code blocks."""
    paragraphs: list[str] = []
    current: list[str] = []
    in_fence = False

    for line in text.split("\n"):
        if re.match(r"^(`{3,}|~{3,})", line):
            in_fence = not in_fence
            current.append(line)
            continue

        if in_fence:
            current.append(line)
            continue

        if not line.strip():
            if current:
                para = "\n".join(current).strip()
                if para:
                    paragraphs.append(para)
                current = []
        else:
            current.append(line)

    if current:
        para = "\n".join(current).strip()
        if para:
            paragraphs.append(para)

    return paragraphs


def _hard_split(text: str, max_size: int) -> list[str]:
    """Split text at max_size boundary without breaking words."""
    chunks: list[str] = []
    while len(text) > max_size:
        split_at = text.rfind(" ", 0, max_size)
        if split_at <= 0:
            split_at = max_size
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks
