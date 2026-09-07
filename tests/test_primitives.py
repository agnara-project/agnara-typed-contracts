"""Tests for primitive type contracts and strict type validation in Agnara 0.1.0a3."""

from __future__ import annotations

import pytest
from agnara.errors import ValidationError
from agnara.schema.standard import PrimitiveSchema, StandardSchemaAdapter


def test_primitive_types_are_supported() -> None:
    """StandardSchemaAdapter supports all JSON-compatible Python primitives plus bytes."""
    adapter = StandardSchemaAdapter()
    for primitive in (bool, int, float, str, bytes):
        assert adapter.supports(primitive)
        schema = adapter.compile(primitive)
        assert isinstance(schema, PrimitiveSchema)
        assert schema.python_type is primitive


def test_primitive_validation_strictness_no_coercion() -> None:
    """Agnara strictly rejects string-encoded numbers; it does NOT coerce."""
    adapter = StandardSchemaAdapter()
    int_schema = adapter.compile(int)

    assert int_schema.validate(42) == 42
    with pytest.raises(ValidationError) as exc_info:
        int_schema.validate("42")
    assert "expected int, got str" in str(exc_info.value)

    float_schema = adapter.compile(float)
    assert float_schema.validate(3.14) == 3.14
    with pytest.raises(ValidationError) as exc_info:
        float_schema.validate("3.14")
    assert "expected float, got str" in str(exc_info.value)


def test_bool_is_not_int() -> None:
    """Even though Python's isinstance(True, int) is True, Agnara rejects bool for int."""
    adapter = StandardSchemaAdapter()
    int_schema = adapter.compile(int)

    with pytest.raises(ValidationError) as exc_info:
        int_schema.validate(True)
    assert "expected int, got bool" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        int_schema.validate(False)
    assert "expected int, got bool" in str(exc_info.value)


def test_int_is_not_float() -> None:
    """Exact type checking means int is not accepted where float is declared."""
    adapter = StandardSchemaAdapter()
    float_schema = adapter.compile(float)

    with pytest.raises(ValidationError) as exc_info:
        float_schema.validate(10)
    assert "expected float, got int" in str(exc_info.value)


def test_bytes_primitive_schema() -> None:
    """bytes is accepted for non-JSON transports and described as binary-formatted string."""
    adapter = StandardSchemaAdapter()
    bytes_schema = adapter.compile(bytes)

    assert bytes_schema.validate(b"signed-token") == b"signed-token"
    assert bytes_schema.json_schema() == {"type": "string", "format": "binary"}

    with pytest.raises(ValidationError) as exc_info:
        bytes_schema.validate("string-instead-of-bytes")
    assert "expected bytes, got str" in str(exc_info.value)


def test_none_primitive_schema() -> None:
    """None accepts only None and maps to null JSON Schema."""
    adapter = StandardSchemaAdapter()
    none_schema = adapter.compile(None)

    assert none_schema.validate(None) is None
    assert none_schema.json_schema() == {"type": "null"}

    with pytest.raises(ValidationError) as exc_info:
        none_schema.validate("something")
    assert "expected None, got str" in str(exc_info.value)
