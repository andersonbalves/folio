"""PEP 750 template processing for PostgreSQL parameterized queries."""

from typing import Any, LiteralString, Protocol, cast, runtime_checkable


@runtime_checkable
class Interpolation(Protocol):
    """Protocol for a single interpolated value in a PEP 750 template."""

    value: Any
    expression: str
    format_spec: str | None
    conversion: str | None


@runtime_checkable
class Template(Protocol):
    """Protocol for a PEP 750 template (t-string)."""

    strings: tuple[str, ...]
    interpolations: tuple[Interpolation, ...]


def postgres_sql(template: Any) -> tuple[LiteralString, tuple[Any, ...]]:
    """Processes a PEP 750 Template object for PostgreSQL.

    Returns a (query_string, parameters) tuple.
    """
    if not hasattr(template, "strings") or not hasattr(template, "interpolations"):
        raise ValueError(f"Object {type(template)} is not a PEP 750 Template")

    query_parts = []
    params = []

    for i, s in enumerate(template.strings):
        query_parts.append(s)
        if i < len(template.interpolations):
            query_parts.append("%s")
            params.append(template.interpolations[i].value)

    return cast(LiteralString, "".join(query_parts)), tuple(params)
