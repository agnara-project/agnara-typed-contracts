"""Tests for collection type contracts and boundaries in Agnara 0.1.0a3."""

from __future__ import annotations

import pytest
from agnara.errors import SchemaError, ValidationError
from agnara.schema.standard import (
    DictionarySchema,
    ListSchema,
    StandardSchemaAdapter,
    TupleSchema,
)


def test_homogeneous_list_schema() -> None:
    """list[T] requires an exact list and validates each element with index tracking."""
    adapter = StandardSchemaAdapter()
    schema = adapter.compile(list[str])
    assert isinstance(schema, ListSchema)
    assert schema.json_schema() == {"type": "array", "items": {"type": "string"}}

    assert schema.validate(["gym", "pool", "wifi"]) == ["gym", "pool", "wifi"]

    # Tuple or set passed where list is declared must be rejected
    with pytest.raises(ValidationError) as exc_info:
        schema.validate(("gym", "pool"))
    assert "expected list, got tuple" in str(exc_info.value)

    # Element validation failure tracks index
    with pytest.raises(ValidationError) as exc_info:
        schema.validate(["gym", 123, "wifi"])
    assert "expected str, got int" in exc_info.value.message
    assert exc_info.value.path == (1,)
    assert exc_info.value.location == "[1]"


def test_string_keyed_dictionary_schema() -> None:
    """dict[str, T] validates homogeneous values with string keys."""
    adapter = StandardSchemaAdapter()
    schema = adapter.compile(dict[str, str])
    assert isinstance(schema, DictionarySchema)
    assert schema.json_schema() == {
        "type": "object",
        "additionalProperties": {"type": "string"},
    }

    assert schema.validate({"tier": "gold", "channel": "web"}) == {
        "tier": "gold",
        "channel": "web",
    }

    # Non-string key raises ValidationError with <key> path
    with pytest.raises(ValidationError) as exc_info:
        schema.validate({101: "invalid-key"})
    assert "expected str key, got int" in exc_info.value.message
    assert exc_info.value.path == ("<key>",)

    # Invalid value type tracks property key in path
    with pytest.raises(ValidationError) as exc_info:
        schema.validate({"tier": 999})
    assert "expected str, got int" in exc_info.value.message
    assert exc_info.value.path == ("tier",)


def test_fixed_length_tuple_schema() -> None:
    """tuple[T1, T2] validates exact length and item types."""
    adapter = StandardSchemaAdapter()
    schema = adapter.compile(tuple[str, int])
    assert isinstance(schema, TupleSchema)
    assert schema.json_schema() == {
        "type": "array",
        "prefixItems": [{"type": "string"}, {"type": "integer"}],
        "items": False,
        "minItems": 2,
        "maxItems": 2,
    }

    assert schema.validate(("2026-09-01", 5)) == ("2026-09-01", 5)

    # Wrong length
    with pytest.raises(ValidationError) as exc_info:
        schema.validate(("2026-09-01", 5, "extra"))
    assert "expected tuple of length 2, got length 3" in str(exc_info.value)

    # Wrong item type with index path
    with pytest.raises(ValidationError) as exc_info:
        schema.validate(("2026-09-01", "five"))
    assert "expected int, got str" in exc_info.value.message
    assert exc_info.value.path == (1,)


def test_variadic_tuple_schema() -> None:
    """tuple[T, ...] validates homogeneous arbitrary-length tuples."""
    adapter = StandardSchemaAdapter()
    schema = adapter.compile(tuple[float, ...])
    assert isinstance(schema, TupleSchema)
    assert schema.variadic is True
    assert schema.json_schema() == {"type": "array", "items": {"type": "number"}}

    assert schema.validate((100.0, 150.5, 200.0)) == (100.0, 150.5, 200.0)

    with pytest.raises(ValidationError) as exc_info:
        schema.validate((100.0, "free", 200.0))
    assert "expected float, got str" in exc_info.value.message
    assert exc_info.value.path == (1,)


def test_unsupported_collections_fail_at_compile_time() -> None:
    """Agnara 0.1.0a3 explicitly rejects dict[non-str, T], set, and frozenset at compile time."""
    adapter = StandardSchemaAdapter()

    # Non-str dictionary keys are rejected
    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(dict[int, str])
    assert "dictionary keys must be str" in str(exc_info.value)

    # Sets are rejected
    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(set[str])
    assert "set is not supported by StandardSchemaAdapter" in str(exc_info.value)

    # Frozensets are rejected
    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(frozenset[str])
    assert "frozenset is not supported by StandardSchemaAdapter" in str(exc_info.value)
