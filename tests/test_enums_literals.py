"""Tests for Enums and Literals in Agnara 0.1.0a3 type contracts."""

from __future__ import annotations

from enum import Enum
from typing import Literal

import pytest
from agnara.errors import SchemaError, ValidationError
from agnara.schema.standard import EnumSchema, LiteralSchema, StandardSchemaAdapter

from domain import PriorityTier, RoomType


def test_strenum_contract_and_validation() -> None:
    """StrEnum compiles to EnumSchema; runtime validation strictly requires the Enum instance."""
    adapter = StandardSchemaAdapter()
    schema = adapter.compile(RoomType)
    assert isinstance(schema, EnumSchema)

    # JSON Schema contains enum values and string type
    doc = schema.json_schema()
    assert doc == {
        "type": "string",
        "enum": ["single", "double", "suite", "deluxe"],
    }

    # Validating enum member instance succeeds
    assert schema.validate(RoomType.SUITE) is RoomType.SUITE

    # Validating raw string fails because StandardSchemaAdapter does not coerce
    with pytest.raises(ValidationError) as exc_info:
        schema.validate("suite")
    assert "expected RoomType, got str" in str(exc_info.value)


def test_literal_contract_and_validation() -> None:
    """Literal[...] compiles to LiteralSchema and validates raw scalar values directly."""
    adapter = StandardSchemaAdapter()
    schema = adapter.compile(PriorityTier)
    assert isinstance(schema, LiteralSchema)

    # JSON Schema contains enum of allowed scalar values
    doc = schema.json_schema()
    assert doc == {"enum": ["standard", "premium", "vip"]}

    # Literal accepts raw strings directly from payload
    assert schema.validate("standard") == "standard"
    assert schema.validate("vip") == "vip"

    # Rejecting values outside the literal set
    with pytest.raises(ValidationError) as exc_info:
        schema.validate("ultra-vip")
    assert "expected one of ('standard', 'premium', 'vip'), got 'ultra-vip'" in str(exc_info.value)


def test_single_literal_produces_const_schema() -> None:
    """A Literal with exactly one scalar value produces a JSON Schema const keyword."""
    adapter = StandardSchemaAdapter()
    schema = adapter.compile(Literal["hotel_booking"])
    assert schema.json_schema() == {"const": "hotel_booking"}
    assert schema.validate("hotel_booking") == "hotel_booking"


def test_unsupported_literal_and_enum_constructs() -> None:
    """Non-JSON-scalar literals and empty/complex enums fail compilation at startup."""
    adapter = StandardSchemaAdapter()

    # Floats are not valid Literal arguments according to typing and Agnara schema
    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(Literal[1.5])  # type: ignore[valid-type]
    assert "literal values must be JSON-compatible values" in str(exc_info.value)

    # Empty enum
    class EmptyEnum(Enum):
        pass

    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(EmptyEnum)
    assert "an enum must define at least one member" in str(exc_info.value)

    # Complex object enum
    class ObjectEnum(Enum):
        COMPLEX = object()

    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(ObjectEnum)
    assert "enum values must be finite JSON scalar values" in str(exc_info.value)


def test_pep695_type_alias_is_unsupported_in_a3() -> None:
    """PEP 695 'type X = ...' generates TypeAliasType which a3 StandardSchemaAdapter rejects."""
    adapter = StandardSchemaAdapter()

    # In Python 3.12+, the 'type' statement creates a TypeAliasType
    type Pep695Tier = Literal["standard", "vip"]

    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(Pep695Tier)

    assert "Pep695Tier is not supported by StandardSchemaAdapter" in str(exc_info.value)
