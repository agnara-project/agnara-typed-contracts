"""Reservation capabilities declared with explicit typed contracts.

This module declares application capabilities for managing hotel and event reservations.
Every capability signature serves a dual purpose in Agnara 0.1.0a3:
1. Static checking: Standard Python static type checkers verify handler call sites.
2. Runtime capability contracts: When ``ExecutionPlan.compile`` runs, ``StandardSchemaAdapter``
   compiles every input parameter's annotation into an immutable, thread-safe ``TypeSchema``
   used for runtime input validation and machine-readable JSON Schema discovery.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Final

from agnara import Agnara, CapabilityId, Risk, StandardEffect
from agnara.core.di import DIRegistry
from agnara.execution.plan import ExecutionPlan

from domain import (
    Guest,
    PriorityTier,
    ReservationConfirmation,
    ReservationStatus,
    RoomType,
)

__all__ = [
    "RESERVATIONS_STORE",
    "app",
    "book_room",
    "calculate_quote",
    "cancel_reservation",
    "compile_plans",
    "lookup_reservation",
]

#: Ephemeral in-memory store simulating a persistence layer
RESERVATIONS_STORE: Final[dict[str, ReservationConfirmation]] = {}

#: Agnara application authoring surface
app = Agnara("reservations")


@app.capability(
    name="book_room",
    risk=Risk.MEDIUM,
    effects=[StandardEffect.DATABASE_WRITE],
    description="Book a verified room reservation with typed guest, dates, rate, and metadata.",
    idempotent=False,
)
def book_room(
    guest: Guest,
    room_type: RoomType,
    stay_dates: tuple[str, str],
    nights: int,
    nightly_rate: float,
    priority: PriorityTier,
    amenities: list[str],
    metadata: dict[str, str],
    special_requests: str | None = None,
    deposit_token: bytes | None = None,
    reference_code: str | int = "RES-AUTO",
) -> ReservationConfirmation:
    """Create and confirm a guest reservation.

    Demonstrates:
    - Nested dataclass parameter (``guest: Guest``)
    - Standard library StrEnum parameter (``room_type: RoomType``)
    - Fixed-length tuple parameter (``stay_dates: tuple[str, str]``)
    - Strict primitive integers and floats (``nights: int``, ``nightly_rate: float``)
    - String Literal scalar parameter (``priority: PriorityTier``)
    - Homogeneous list of strings (``amenities: list[str]``)
    - String-keyed homogeneous dictionary (``metadata: dict[str, str]``)
    - Optional string with None default (``special_requests: str | None = None``)
    - Optional bytes primitive (``deposit_token: bytes | None = None``)
    - Union parameter with default (``reference_code: str | int = "RES-AUTO"``)
    - Return contract: ``ReservationConfirmation`` dataclass
    """
    reservation_id = f"res_{uuid.uuid4().hex[:8]}"
    subtotal = nights * nightly_rate
    tax_and_fees = subtotal * 0.10
    total_amount = round(subtotal + tax_and_fees, 2)

    confirmation = ReservationConfirmation(
        reservation_id=reservation_id,
        guest_name=guest.name,
        room_type=room_type,
        nights=nights,
        total_amount=total_amount,
        status=ReservationStatus.CONFIRMED,
        priority=priority,
        amenities=list(amenities),
        metadata=dict(metadata),
        special_requests=special_requests,
        reference_code=reference_code,
    )
    RESERVATIONS_STORE[reservation_id] = confirmation
    if isinstance(reference_code, str):
        RESERVATIONS_STORE[reference_code] = confirmation
    elif isinstance(reference_code, int):
        RESERVATIONS_STORE[str(reference_code)] = confirmation

    return confirmation


@app.capability(
    name="cancel_reservation",
    risk=Risk.MEDIUM,
    effects=[StandardEffect.DATABASE_WRITE],
    description="Cancel an active reservation by ID, returning None upon success.",
    idempotent=True,
)
def cancel_reservation(
    reservation_id: str,
    reason: str | None = None,
) -> None:
    """Cancel an existing reservation.

    Demonstrates:
    - Primitive string parameter (``reservation_id: str``)
    - Optional string parameter (``reason: str | None = None``)
    - Return contract annotated as ``-> None`` (compiled to ``NoneSchema``)
    """
    if reservation_id in RESERVATIONS_STORE:
        existing = RESERVATIONS_STORE[reservation_id]
        updated = ReservationConfirmation(
            reservation_id=existing.reservation_id,
            guest_name=existing.guest_name,
            room_type=existing.room_type,
            nights=existing.nights,
            total_amount=existing.total_amount,
            status=ReservationStatus.CANCELLED,
            priority=existing.priority,
            amenities=existing.amenities,
            metadata=existing.metadata,
            special_requests=f"Cancelled: {reason}" if reason else "Cancelled",
            reference_code=existing.reference_code,
        )
        RESERVATIONS_STORE[reservation_id] = updated


@app.capability(
    name="calculate_quote",
    risk=Risk.LOW,
    effects=[StandardEffect.READ],
    description="Calculate estimated quote across variadic nightly rates.",
    idempotent=True,
)
def calculate_quote(
    rates: tuple[float, ...],
    discount_percentage: float = 0.0,
) -> float:
    """Calculate total stay cost from variadic nightly rates.

    Demonstrates:
    - Variadic homogeneous tuple parameter (``rates: tuple[float, ...]``)
    - Primitive float parameter with default (``discount_percentage: float = 0.0``)
    - Return contract: primitive ``float``
    """
    subtotal = sum(rates)
    discount = subtotal * (discount_percentage / 100.0)
    return round(subtotal - discount, 2)


@app.capability(
    name="lookup_reservation",
    risk=Risk.LOW,
    effects=[StandardEffect.READ],
    description="Look up an existing reservation by alphanumeric code or numeric ID.",
    idempotent=True,
)
def lookup_reservation(
    identifier: str | int,
) -> ReservationConfirmation | None:
    """Find a reservation by string code or numeric ID.

    Demonstrates:
    - Union parameter input (``identifier: str | int``)
    - Union return contract (``ReservationConfirmation | None``)
    """
    lookup_key = str(identifier)
    return RESERVATIONS_STORE.get(lookup_key)


def compile_plans(
    target_app: Agnara | None = None,
    registry: DIRegistry | None = None,
) -> Mapping[CapabilityId, ExecutionPlan]:
    """Compile an Agnara app into immutable ExecutionPlan instances."""
    active_app = target_app if target_app is not None else app
    di_registry = registry if registry is not None else DIRegistry()
    frozen_registry = active_app.compile()

    compiled: dict[CapabilityId, ExecutionPlan] = {}
    for cap_id, definition in frozen_registry.items():
        compiled[cap_id] = ExecutionPlan.compile(definition, di_registry)
    return compiled
