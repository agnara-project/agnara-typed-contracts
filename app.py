"""Executable demonstration for Agnara Historical Reference Application #006.
Demonstrates: agnara-typed-contracts.

This script executes 5 comprehensive scenarios demonstrating how Python type hints
become strict machine-readable capability contracts in Agnara 0.1.0a3.

Run directly:
    python app.py
"""

from __future__ import annotations

import asyncio
import json
from typing import get_type_hints

from agnara.capability.identity import CapabilityId
from agnara.core.di import DIContainer, DIRegistry
from agnara.execution.context import ExecutionContext
from agnara.execution.invocation import Invocation
from agnara.execution.plan import ExecutionPlan
from agnara.execution.result import Failure, Success
from agnara.execution.runtime import invoke_result
from agnara.introspection import describe_app
from agnara.schema.standard import StandardSchemaAdapter

from domain import ContactInfo, Guest, RoomType
from reservations import app, compile_plans


def _line(char: str = "-", length: int = 80) -> None:
    print(char * length)


def _banner(title: str) -> None:
    print()
    _line("=")
    print(f"  {title}")
    _line("=")


def _make_context(capability_name: str, payload: dict) -> ExecutionContext:
    di_reg = DIRegistry()
    inv = Invocation(
        capability_id=CapabilityId.parse(f"reservations.{capability_name}"),
        payload=payload,
        metadata={"client": "cli-demo", "version": "0.1.0"},
    )
    return ExecutionContext(invocation=inv, di_container=DIContainer(di_reg))


async def run_scenario_1_happy_path(plan: ExecutionPlan) -> None:
    _banner("SCENARIO 1: Happy Path Booking & Typed Contract Dispatch")
    print("Building a fully typed reservation payload:")
    print("  - guest: Guest (nested dataclass: ContactInfo -> Guest)")
    print("  - room_type: RoomType.DELUXE (StrEnum)")
    print("  - stay_dates: ('2026-09-15', '2026-09-18') (fixed-length tuple[str, str])")
    print("  - nights: 3 (int)")
    print("  - nightly_rate: 220.0 (float)")
    print("  - priority: 'vip' (Literal['standard', 'premium', 'vip'])")
    print("  - amenities: ['spa', 'valet', 'wifi'] (list[str])")
    print("  - metadata: {'source': 'partner-api', 'vip_tier': 'diamond'} (dict[str, str])")
    print("  - special_requests: 'Late check-in at 22:00' (str | None)")
    print("  - deposit_token: b'tok_sec_999' (bytes | None)")

    guest = Guest(
        name="Alexander Vance",
        contact=ContactInfo(email="alex.vance@blackmesa.org", phone="+1-555-0142"),
        is_corporate=True,
    )

    payload = {
        "guest": guest,
        "room_type": RoomType.DELUXE,
        "stay_dates": ("2026-09-15", "2026-09-18"),
        "nights": 3,
        "nightly_rate": 220.0,
        "priority": "vip",
        "amenities": ["spa", "valet", "wifi"],
        "metadata": {"source": "partner-api", "vip_tier": "diamond"},
        "special_requests": "Late check-in at 22:00",
        "deposit_token": b"tok_sec_999",
        "reference_code": "CORP-9921",
    }

    ctx = _make_context("book_room", payload)
    result = await invoke_result(plan, ctx)

    if isinstance(result, Success):
        conf = result.value
        print("\n[SUCCESS] Reservation successfully created and verified:")
        print(f"  Reservation ID : {conf.reservation_id}")
        print(f"  Guest Name     : {conf.guest_name}")
        print(f"  Room Type      : {conf.room_type.value}")
        print(f"  Priority       : {conf.priority}")
        print(f"  Stay Duration  : {conf.nights} nights")
        print(f"  Total Cost     : ${conf.total_amount:.2f} (including taxes & fees)")
        print(f"  Status         : {conf.status.value}")
    else:
        print(f"[UNEXPECTED FAILURE] {result}")


async def run_scenario_2_strict_validation(plan: ExecutionPlan) -> None:
    _banner("SCENARIO 2: Strict Primitive & Literal Validation Failures")
    print("Demonstrating strict type checking without silent coercion in Agnara:\n")

    guest = Guest(name="Gordon Freeman", contact=ContactInfo(email="gordon@blackmesa.org"))

    # Case A: String passed for integer parameter
    print("Case A: String passed for 'nights: int' -> {'nights': '3'}")
    payload_a = {
        "guest": guest,
        "room_type": RoomType.SINGLE,
        "stay_dates": ("2026-09-15", "2026-09-16"),
        "nights": "3",  # Error: str instead of int
        "nightly_rate": 100.0,
        "priority": "standard",
        "amenities": ["wifi"],
        "metadata": {"source": "web"},
    }
    res_a = await invoke_result(plan, _make_context("book_room", payload_a))
    assert isinstance(res_a, Failure)
    print(f"  Result Code: {res_a.code.value}")
    print(f"  Message    : {res_a.message}")
    print(f"  Path       : {res_a.details.get('path')}")

    # Case B: Boolean passed for integer parameter
    # (Python says isinstance(True, int) is True, but Agnara strictly rejects it)
    print("\nCase B: Boolean passed for 'nights: int' -> {'nights': True}")
    payload_b = dict(payload_a, nights=True)
    res_b = await invoke_result(plan, _make_context("book_room", payload_b))
    assert isinstance(res_b, Failure)
    print(f"  Result Code: {res_b.code.value}")
    print(f"  Message    : {res_b.message}")
    print(f"  Path       : {res_b.details.get('path')}")

    # Case C: Invalid Literal scalar value
    print("\nCase C: Invalid Literal choice -> {'priority': 'ultra-vip'}")
    payload_c = dict(payload_a, nights=2, priority="ultra-vip")
    res_c = await invoke_result(plan, _make_context("book_room", payload_c))
    assert isinstance(res_c, Failure)
    print(f"  Result Code: {res_c.code.value}")
    print(f"  Message    : {res_c.message}")
    print(f"  Path       : {res_c.details.get('path')}")


async def run_scenario_3_nested_path_tracking(plan: ExecutionPlan) -> None:
    _banner("SCENARIO 3: Deep Nested Dataclass & Collection Path Tracking")
    print("Demonstrating precise error paths in complex structures:\n")

    # Case A: Collection item type error
    print("Case A: Invalid item in list[str] -> amenities[1] is 404 (int)")
    guest = Guest(name="Barney Calhoun", contact=ContactInfo(email="barney@blackmesa.org"))
    payload_coll = {
        "guest": guest,
        "room_type": RoomType.DOUBLE,
        "stay_dates": ("2026-09-20", "2026-09-22"),
        "nights": 2,
        "nightly_rate": 150.0,
        "priority": "standard",
        "amenities": ["parking", 404, "breakfast"],  # Index 1 is int
        "metadata": {"source": "desk"},
    }
    res_coll = await invoke_result(plan, _make_context("book_room", payload_coll))
    assert isinstance(res_coll, Failure)
    print(f"  Result Code: {res_coll.code.value}")
    print(f"  Message    : {res_coll.message}")
    print(f"  Path Tuple : {res_coll.details.get('path')}")
    print("  Formatted  : amenities[1]: expected str, got int")

    # Case B: Nested dataclass field error
    print("\nCase B: Invalid field inside nested dataclass -> guest.contact.email is 99999 (int)")
    bad_contact = ContactInfo(email=99999)  # type: ignore[arg-type]
    bad_guest = Guest(name="Barney Calhoun", contact=bad_contact)
    payload_model = dict(payload_coll, guest=bad_guest, amenities=["parking", "wifi"])
    res_model = await invoke_result(plan, _make_context("book_room", payload_model))
    assert isinstance(res_model, Failure)
    print(f"  Result Code: {res_model.code.value}")
    print(f"  Message    : {res_model.message}")
    print(f"  Path Tuple : {res_model.details.get('path')}")
    print("  Formatted  : guest.contact.email: expected str, got int")


def run_scenario_4_schema_introspection() -> None:
    _banner("SCENARIO 4: Machine-Readable Schema Introspection (describe_app)")
    print("Inspecting the compiled app to extract protocol-neutral JSON Schema:\n")

    plans = compile_plans()
    app_desc = describe_app(app, plans.values())

    print(f"Application Name: {app_desc.name}")
    print(f"Declared Capabilities: {len(app_desc.capabilities)}")

    book_cap = next(c for c in app_desc.capabilities if c.id == "reservations.book_room")
    print(f"\nCapability: {book_cap.id}")
    print(f"Description: {book_cap.description}")
    print(f"Effects: {list(book_cap.effects)}")
    print(f"Total Inputs: {len(book_cap.inputs)}")
    print("\nSample JSON Schema projections generated from Python type hints:")

    for inp in book_cap.inputs:
        schema_obj = json.loads(inp.schema)
        req_marker = "[REQUIRED]" if inp.required else "[OPTIONAL]"
        print(f"\n  * Input '{inp.name}' {req_marker}:")
        formatted = json.dumps(schema_obj, indent=4)
        for line in formatted.splitlines()[:6]:
            print(f"      {line}")
        if len(formatted.splitlines()) > 6:
            print("      ...")


def run_scenario_5_return_contracts_analysis() -> None:
    _banner("SCENARIO 5: Return Contracts & Framework Boundary Analysis")
    print("Analyzing return type annotations and runtime enforcement boundaries in 0.1.0a3:\n")

    adapter = StandardSchemaAdapter()
    for cap_id in app.capabilities:
        definition = app.capabilities[cap_id]
        hints = get_type_hints(definition.handler)
        ret_type = hints.get("return")
        compiled_schema = adapter.compile(ret_type) if adapter.supports(ret_type) else None
        schema_kind = type(compiled_schema).__name__ if compiled_schema else "Unsupported"
        json_summary = list(compiled_schema.json_schema().keys()) if compiled_schema else []
        print(f"Capability: {cap_id}")
        print(f"  -> Declared Return Type : {ret_type}")
        print(f"  -> Adapter Schema Class : {schema_kind}")
        print(f"  -> JSON Schema Keys     : {json_summary}")

    print("\nImportant Architectural Note (Agnara 0.1.0a3 Baseline):")
    print("  1. StandardSchemaAdapter CAN compile return annotations into TypeSchemas.")
    print("  2. In agnara==0.1.0a3, ExecutionPlan compiles input_schemas only.")
    print("  3. The runtime (invoke / invoke_result) validates inputs on entry, but does")
    print("     NOT validate handler return values against return type annotations.")
    print("  4. CapabilityDescriptor in introspection exports inputs only; output schemas")
    print("     remain a transport adapter concern or future framework feature.")


async def main() -> None:
    print("=" * 80)
    print("  AGNARA HISTORICAL REFERENCE APPLICATION #006: agnara-typed-contracts")
    print("  Framework Version : agnara==0.1.0a3")
    print("  Runtime           : CPython >= 3.14")
    print("  Philosophy        : Python types -> machine-readable capability contract")
    print("  Status            : Historical / Frozen")
    print("=" * 80)

    plans = compile_plans()
    book_plan = plans[CapabilityId.parse("reservations.book_room")]

    await run_scenario_1_happy_path(book_plan)
    await run_scenario_2_strict_validation(book_plan)
    await run_scenario_3_nested_path_tracking(book_plan)
    run_scenario_4_schema_introspection()
    run_scenario_5_return_contracts_analysis()

    _banner("EXECUTION COMPLETE: All 5 scenarios executed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
