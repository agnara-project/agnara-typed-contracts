"""Tests for input validation error behavior and canonical Failure projections."""

from __future__ import annotations

import asyncio

from agnara.capability.identity import CapabilityId
from agnara.core.di import DIContainer, DIRegistry
from agnara.errors import ValidationError
from agnara.execution.context import ExecutionContext
from agnara.execution.invocation import Invocation
from agnara.execution.result import FailureCode
from agnara.execution.runtime import invoke_result

from domain import ContactInfo, Guest, RoomType
from reservations import compile_plans


def _make_context(capability_name: str, payload: dict) -> ExecutionContext:
    """Helper to assemble an ExecutionContext for testing."""
    di_reg = DIRegistry()
    inv = Invocation(
        capability_id=CapabilityId.parse(f"reservations.{capability_name}"),
        payload=payload,
        metadata={},
    )
    return ExecutionContext(invocation=inv, di_container=DIContainer(di_reg))


def test_missing_required_input_fails() -> None:
    """Missing a required capability input yields Failure(INVALID_INPUT) with path."""

    async def _run() -> None:
        plans = compile_plans()
        plan = plans[CapabilityId.parse("reservations.cancel_reservation")]

        # cancel_reservation requires 'reservation_id'
        ctx = _make_context("cancel_reservation", {})
        result = await invoke_result(plan, ctx)

        assert result.code == FailureCode.INVALID_INPUT
        assert result.message == "required input is missing"
        assert result.details.get("path") == ("reservation_id",)

    asyncio.run(_run())


def test_unexpected_input_fails() -> None:
    """Supplying unexpected parameters in payload yields Failure(INVALID_INPUT)."""

    async def _run() -> None:
        plans = compile_plans()
        plan = plans[CapabilityId.parse("reservations.cancel_reservation")]

        ctx = _make_context(
            "cancel_reservation",
            {"reservation_id": "res_123", "unknown_rogue_param": "forbidden"},
        )
        result = await invoke_result(plan, ctx)

        assert result.code == FailureCode.INVALID_INPUT
        assert result.message == "unexpected input"
        assert result.details.get("path") == ("unknown_rogue_param",)

    asyncio.run(_run())


def test_primitive_type_mismatch_fails() -> None:
    """Primitive type mismatch in payload reports exact parameter in error path."""

    async def _run() -> None:
        plans = compile_plans()
        plan = plans[CapabilityId.parse("reservations.book_room")]

        guest = Guest(name="Alice", contact=ContactInfo(email="alice@agnara.dev"))
        payload = {
            "guest": guest,
            "room_type": RoomType.SINGLE,
            "stay_dates": ("2026-09-10", "2026-09-12"),
            "nights": "two",  # Expected int, got str
            "nightly_rate": 150.0,
            "priority": "standard",
            "amenities": ["wifi"],
            "metadata": {"source": "web"},
        }
        ctx = _make_context("book_room", payload)
        result = await invoke_result(plan, ctx)

        assert result.code == FailureCode.INVALID_INPUT
        assert "expected int, got str" in result.message
        assert result.details.get("path") == ("nights",)

    asyncio.run(_run())


def test_collection_index_error_path() -> None:
    """Invalid item in list payload preserves item index in Failure path."""

    async def _run() -> None:
        plans = compile_plans()
        plan = plans[CapabilityId.parse("reservations.book_room")]

        guest = Guest(name="Alice", contact=ContactInfo(email="alice@agnara.dev"))
        payload = {
            "guest": guest,
            "room_type": RoomType.SINGLE,
            "stay_dates": ("2026-09-10", "2026-09-12"),
            "nights": 2,
            "nightly_rate": 150.0,
            "priority": "standard",
            "amenities": ["wifi", 999, "breakfast"],  # Index 1 is an int
            "metadata": {"source": "web"},
        }
        ctx = _make_context("book_room", payload)
        result = await invoke_result(plan, ctx)

        assert result.code == FailureCode.INVALID_INPUT
        assert "expected str, got int" in result.message
        assert result.details.get("path") == ("amenities", 1)

    asyncio.run(_run())


def test_nested_dataclass_error_path() -> None:
    """Invalid field inside a nested dataclass preserves the entire attribute path."""

    async def _run() -> None:
        plans = compile_plans()
        plan = plans[CapabilityId.parse("reservations.book_room")]

        bad_contact = ContactInfo(email=True)  # type: ignore[arg-type]
        bad_guest = Guest(name="Alice", contact=bad_contact)
        payload = {
            "guest": bad_guest,
            "room_type": RoomType.SINGLE,
            "stay_dates": ("2026-09-10", "2026-09-12"),
            "nights": 2,
            "nightly_rate": 150.0,
            "priority": "standard",
            "amenities": ["wifi"],
            "metadata": {"source": "web"},
        }
        ctx = _make_context("book_room", payload)
        result = await invoke_result(plan, ctx)

        assert result.code == FailureCode.INVALID_INPUT
        assert "expected str, got bool" in result.message
        assert result.details.get("path") == ("guest", "contact", "email")

    asyncio.run(_run())


def test_validation_error_formatting() -> None:
    """Direct tests on ValidationError location formatting and segment chaining."""
    err = ValidationError("type error", path=("booking", 0, "amenity"))
    assert err.location == "booking[0].amenity"
    assert str(err) == "booking[0].amenity: type error"

    promoted = err.at("root")
    assert promoted.path == ("root", "booking", 0, "amenity")
    assert promoted.location == "root.booking[0].amenity"
