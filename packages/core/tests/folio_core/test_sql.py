"""Tests for folio_core/sql.py — postgres_sql() processes PEP 750 Template objects."""

import pytest
from folio_core.sql import postgres_sql


class _Interp:
    """Minimal Interpolation protocol implementation for testing."""

    def __init__(self, value):
        self.value = value
        self.expression = repr(value)
        self.format_spec = None
        self.conversion = None


class _Template:
    """Minimal Template protocol implementation for testing."""

    def __init__(self, strings: tuple[str, ...], *values):
        self.strings = strings
        self.interpolations = tuple(_Interp(v) for v in values)


def test_single_interpolation():
    t = _Template(("SELECT * FROM t WHERE id = ", ""), 42)
    query, params = postgres_sql(t)
    assert query == "SELECT * FROM t WHERE id = %s"
    assert params == (42,)


def test_multiple_interpolations():
    t = _Template(("SELECT * FROM t WHERE a = ", " AND b = ", ""), "foo", 99)
    query, params = postgres_sql(t)
    assert query == "SELECT * FROM t WHERE a = %s AND b = %s"
    assert params == ("foo", 99)


def test_no_interpolations():
    t = _Template(("SELECT 1",))
    query, params = postgres_sql(t)
    assert query == "SELECT 1"
    assert params == ()


def test_invalid_input_raises_value_error():
    with pytest.raises(ValueError, match="not a PEP 750 Template"):
        postgres_sql("not a template")
