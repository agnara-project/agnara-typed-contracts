"""Tests for return contracts, adapter compilation, and runtime non-enforcement in 0.1.0a3."""

from __future__ import annotations

import asyncio
from typing import get_type_hints

from agnara import Agnara
from agnara.capability.identity import CapabilityId
from agnara.core.di import DIContainer, DIRegistry
from agnara.execution.context import ExecutionContext
from agnara.execution.invocation import Invocation
from agnara.execution.plan import ExecutionPlan
from agnara.execution.result import Success
from agnara.execution.runtime import invoke, invoke_result
from agnara.schema.standard import (
    DataclassSchema,
    NoneSchema,
    PrimitiveSchema,
    StandardSchemaAdapter,
    UnionSchema,
)

from reservations import (
    book_room,
    calculate_quote,
    cancel_reservation,
    compile_plans,
    lookup_reservation,
)


def test_return_type_hints_can_be_compiled_by_adapter() -> None:
    """StandardSchemaAdapter successfully compiles return type annotations."""
    adapter = StandardSchemaAdapter()

    # cancel_reservation -> None
    hints_cancel = get_type_hints(cancel_reservation)
    schema_cancel = adapter.compile(hints_cancel["return"])
    assert isinstance(schema_cancel, NoneSchema)
    assert schema_cancel.json_schema() == {"type": "null"}

    # book_room -> ReservationConfirmation
    hints_book = get_type_hints(book_room)
    schema_book = adapter.compile(hints_book["return"])
    assert isinstance(schema_book, DataclassSchema)
    assert schema_book.json_schema()["type"] == "object"

    # calculate_quote -> float
    hints_quote = get_type_hints(calculate_quote)
    schema_quote = adapter.compile(hints_quote["return"])
    assert isinstance(schema_quote, PrimitiveSchema)
    assert schema_quote.json_schema() == {"type": "number"}

    # lookup_reservation -> ReservationConfirmation | None
    hints_lookup = get_type_hints(lookup_reservation)
    schema_lookup = adapter.compile(hints_lookup["return"])
    assert isinstance(schema_lookup, UnionSchema)
    assert "anyOf" in schema_lookup.json_schema()


def test_execution_plan_does_not_hold_return_schema_in_a3() -> None:
    """In agnara==0.1.0a3, ExecutionPlan compiles input_schemas only; no return schema is stored."""
    plans = compile_plans()
    plan = plans[CapabilityId.parse("reservations.book_room")]

    # input_schemas and required_inputs are present
    assert hasattr(plan, "input_schemas")
    assert hasattr(plan, "required_inputs")

    # Return schemas are not part of ExecutionPlan in a3
    assert not hasattr(plan, "output_schema")
    assert not hasattr(plan, "return_schema")
    assert not hasattr(plan, "output_schemas")


def test_runtime_does_not_enforce_return_types_in_a3() -> None:
    """The runtime does NOT validate handler return values against return type annotations in a3.

    This test explicitly documents the historical boundary of 0.1.0a3:
    input contracts are strictly validated at invocation time, while return type
    checking remains a domain/adapter concern or future feature.
    """

    async def _run() -> None:
        test_app = Agnara("return_test")

        # Declare capability claiming to return int, but returning a string
        @test_app.capability()
        def mismatched_return_handler() -> int:
            return "this is a string, not an int"  # type: ignore[return-value]

        frozen = test_app.compile()
        reg = DIRegistry()
        plan = ExecutionPlan.compile(frozen["return_test.mismatched_return_handler"], reg)
        ctx = ExecutionContext(
            Invocation(
                CapabilityId.parse("return_test.mismatched_return_handler"),
                payload={},
                metadata={},
            ),
            di_container=DIContainer(reg),
        )

        # In invoke(): returns the raw mismatched string without raising ValidationError
        raw_result = await invoke(plan, ctx)
        assert raw_result == "this is a string, not an int"

        # In invoke_result(): wraps in Success without failing
        canonical_result = await invoke_result(plan, ctx)
        assert isinstance(canonical_result, Success)
        assert canonical_result.value == "this is a string, not an int"

    asyncio.run(_run())
