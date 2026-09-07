"""Tests for Agnara introspection and machine-readable JSON Schema discovery."""

from __future__ import annotations

import json

from agnara.introspection import AppDescriptor, describe_app
from agnara.introspection.descriptors import CapabilityDescriptor, InputDescriptor

from reservations import app, compile_plans


def test_describe_app_generates_valid_descriptors() -> None:
    """describe_app builds an immutable AppDescriptor with machine-readable InputDescriptors."""
    plans = compile_plans()
    app_desc = describe_app(app, plans.values())

    assert isinstance(app_desc, AppDescriptor)
    assert app_desc.name == "reservations"
    assert len(app_desc.capabilities) == 4

    cap_by_id: dict[str, CapabilityDescriptor] = {cap.id: cap for cap in app_desc.capabilities}
    assert "reservations.book_room" in cap_by_id
    assert "reservations.cancel_reservation" in cap_by_id
    assert "reservations.calculate_quote" in cap_by_id
    assert "reservations.lookup_reservation" in cap_by_id


def test_input_descriptors_and_json_schema_fidelity() -> None:
    """Every capability input produces a valid JSON Schema matching the Python annotation."""
    plans = compile_plans()
    app_desc = describe_app(app, plans.values())
    cap_by_id = {cap.id: cap for cap in app_desc.capabilities}

    book_cap = cap_by_id["reservations.book_room"]
    inputs_by_name: dict[str, InputDescriptor] = {inp.name: inp for inp in book_cap.inputs}

    # nights: int (required, integer schema)
    nights_inp = inputs_by_name["nights"]
    assert nights_inp.required is True
    nights_schema = json.loads(nights_inp.schema)
    assert nights_schema == {"type": "integer"}

    # special_requests: str | None = None (optional, anyOf schema)
    req_inp = inputs_by_name["special_requests"]
    assert req_inp.required is False
    req_schema = json.loads(req_inp.schema)
    assert "anyOf" in req_schema
    assert {"type": "string"} in req_schema["anyOf"]
    assert {"type": "null"} in req_schema["anyOf"]

    # priority: PriorityTier (Literal)
    prio_inp = inputs_by_name["priority"]
    assert prio_inp.required is True
    prio_schema = json.loads(prio_inp.schema)
    assert prio_schema == {"enum": ["standard", "premium", "vip"]}

    # amenities: list[str]
    amenities_inp = inputs_by_name["amenities"]
    assert amenities_inp.required is True
    amenities_schema = json.loads(amenities_inp.schema)
    assert amenities_schema == {"type": "array", "items": {"type": "string"}}

    # metadata: dict[str, str]
    meta_inp = inputs_by_name["metadata"]
    assert meta_inp.required is True
    meta_schema = json.loads(meta_inp.schema)
    assert meta_schema == {
        "type": "object",
        "additionalProperties": {"type": "string"},
    }

    # stay_dates: tuple[str, str]
    dates_inp = inputs_by_name["stay_dates"]
    assert dates_inp.required is True
    dates_schema = json.loads(dates_inp.schema)
    assert dates_schema == {
        "type": "array",
        "prefixItems": [{"type": "string"}, {"type": "string"}],
        "items": False,
        "minItems": 2,
        "maxItems": 2,
    }

    # guest: Guest (dataclass)
    guest_inp = inputs_by_name["guest"]
    assert guest_inp.required is True
    guest_schema = json.loads(guest_inp.schema)
    assert guest_schema["type"] == "object"
    assert guest_schema["additionalProperties"] is False
    assert "name" in guest_schema["properties"]
    assert "contact" in guest_schema["properties"]


def test_capability_descriptor_has_no_output_descriptor_in_a3() -> None:
    """In 0.1.0a3, CapabilityDescriptor exports inputs only, with no outputs field."""
    plans = compile_plans()
    app_desc = describe_app(app, plans.values())
    cap = app_desc.capabilities[0]

    # Has inputs, dependencies, policies, exposures
    assert hasattr(cap, "inputs")
    assert hasattr(cap, "dependencies")
    assert hasattr(cap, "policies")
    assert hasattr(cap, "exposures")

    # Has NO outputs or return_schema
    assert not hasattr(cap, "output")
    assert not hasattr(cap, "outputs")
    assert not hasattr(cap, "return_schema")


def test_app_descriptor_json_serialization() -> None:
    """AppDescriptor can be cleanly serialized to JSON data without runtime artifacts."""
    plans = compile_plans()
    app_desc = describe_app(app, plans.values())
    data = app_desc.json_data()

    assert data["name"] == "reservations"
    assert isinstance(data["capabilities"], list)
    assert len(data["capabilities"]) == 4

    # Verify JSON serializability
    serialized = json.dumps(data)
    assert isinstance(serialized, str)
    assert "reservations.book_room" in serialized
