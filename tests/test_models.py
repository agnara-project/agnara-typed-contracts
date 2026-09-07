"""Tests for dataclass contracts, nesting, and boundaries in Agnara 0.1.0a3."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from typing import Optional

import pytest
from agnara.errors import SchemaError, ValidationError
from agnara.schema.standard import DataclassSchema, StandardSchemaAdapter

from domain import ContactInfo, Guest


def test_dataclass_exact_instance_requirement() -> None:
    """DataclassSchema requires an exact dataclass instance; it does NOT parse raw dicts."""
    adapter = StandardSchemaAdapter()
    schema = adapter.compile(ContactInfo)
    assert isinstance(schema, DataclassSchema)

    valid = ContactInfo(email="guest@agnara.dev", phone="+1-555-0199")
    assert schema.validate(valid) == valid

    # Passing a dict must fail rather than silently instantiating
    with pytest.raises(ValidationError) as exc_info:
        schema.validate({"email": "guest@agnara.dev", "phone": "+1-555-0199"})
    assert "expected ContactInfo, got dict" in str(exc_info.value)


def test_dataclass_json_schema_required_fields() -> None:
    """Fields without defaults are required; fields with defaults are optional in JSON Schema."""
    adapter = StandardSchemaAdapter()
    contact_schema = adapter.compile(ContactInfo)
    doc = contact_schema.json_schema()

    assert doc["type"] == "object"
    assert doc["additionalProperties"] is False
    assert "email" in doc["properties"]
    assert "phone" in doc["properties"]
    # email has no default -> required; phone defaults to None -> not in required
    assert doc.get("required") == ["email"]

    guest_schema = adapter.compile(Guest)
    guest_doc = guest_schema.json_schema()
    assert guest_doc["type"] == "object"
    # name and contact have no default -> required; is_corporate defaults to False -> optional
    assert sorted(guest_doc["required"]) == ["contact", "name"]
    # nested contact property is also an object schema
    assert guest_doc["properties"]["contact"]["type"] == "object"


def test_nested_dataclass_validation_and_path_reporting() -> None:
    """Validating nested dataclasses preserves the full field path on errors."""
    adapter = StandardSchemaAdapter()
    guest_schema = adapter.compile(Guest)

    # Valid nested model
    guest = Guest(
        name="Elena Rostova",
        contact=ContactInfo(email="elena@example.com", phone="+1-555-1234"),
        is_corporate=True,
    )
    assert guest_schema.validate(guest) == guest

    # Error in deeply nested field (contact.email is not str)
    bad_contact = ContactInfo(email=12345, phone="+1-555-1234")  # type: ignore[arg-type]
    bad_guest = Guest(name="Elena Rostova", contact=bad_contact)

    with pytest.raises(ValidationError) as exc_info:
        guest_schema.validate(bad_guest)

    assert exc_info.value.path == ("contact", "email")
    assert exc_info.value.location == "contact.email"
    assert "expected str, got int" in exc_info.value.message


@dataclass
class RecursiveNode:
    val: int
    next: Optional[RecursiveNode] = None


def test_unsupported_recursive_dataclass_fails_at_compile_time() -> None:
    """Recursive dataclass graphs are rejected at compile time (ADR 0005)."""
    adapter = StandardSchemaAdapter()

    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(RecursiveNode)

    assert "recursive dataclass graph: RecursiveNode -> RecursiveNode" in str(exc_info.value)


def test_unsupported_init_var_fails_at_compile_time() -> None:
    """Dataclasses with InitVar require directional schema support and fail in 0.1.0a3."""
    adapter = StandardSchemaAdapter()

    @dataclass
    class WithInitVar:
        name: str
        token: InitVar[str]

    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(WithInitVar)

    assert "InitVar fields require directional schema support: token" in str(exc_info.value)


def test_unsupported_init_false_fails_at_compile_time() -> None:
    """Dataclasses with init=False fields fail at compile time."""
    adapter = StandardSchemaAdapter()

    @dataclass
    class WithInitFalse:
        name: str
        computed: str = field(init=False, default="")

    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(WithInitFalse)

    assert "uses init=False, which requires directional schema support" in str(exc_info.value)


def test_unsupported_third_party_models_fail_at_compile_time() -> None:
    """Arbitrary classes that are not dataclasses fail compilation (keeping core lean, ADR 0004)."""
    adapter = StandardSchemaAdapter()

    class OrdinaryClass:
        def __init__(self, name: str) -> None:
            self.name = name

    with pytest.raises(SchemaError) as exc_info:
        adapter.compile(OrdinaryClass)

    assert "is not supported by StandardSchemaAdapter" in str(exc_info.value)
