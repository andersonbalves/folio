from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Interpolation(Protocol):
    value: Any
    expression: str
    format_spec: str | None
    conversion: str | None


@runtime_checkable
class Template(Protocol):
    strings: tuple[str, ...]
    interpolations: tuple[Interpolation, ...]


def postgres_sql(template: Any) -> tuple[str, tuple[Any, ...]]:
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

    return "".join(query_parts), tuple(params)
