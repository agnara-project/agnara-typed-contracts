"""Domain models, enums, and types for the reservation system.

This module defines the pure domain structures used to declare capability contracts
in Agnara 0.1.0a3. In Agnara, capability authoring is decoupled from serialization
frameworks (ADR 0004):
1. No external model libraries (Pydantic, msgspec) are required or used in core.
2. Standard library `@dataclass` classes serve as structural models.
3. Standard library `enum.StrEnum` classes represent discrete domain classifications.
4. `typing.Literal` defines exact scalar choices suitable for wire payloads.
5. `T | None` expresses optionality without external wrappers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

__all__ = [
    "BookingChannel",
    "ContactInfo",
    "Guest",
    "PriorityTier",
    "ReservationConfirmation",
    "ReservationStatus",
    "RoomType",
]


class RoomType(StrEnum):
    """Enumeration of available accommodation tiers."""

    SINGLE = "single"
    DOUBLE = "double"
    SUITE = "suite"
    DELUXE = "deluxe"


class ReservationStatus(StrEnum):
    """Lifecycle state of a guest booking."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class BookingChannel(StrEnum):
    """Originating channel for incoming booking requests."""

    DIRECT = "direct"
    WEB = "web"
    MOBILE = "mobile"
    CORPORATE = "corporate"


#: Scalar priority level accepted directly in raw payload dispatches.
#: Note: In Agnara 0.1.0a3, typing.Literal is supported directly, whereas PEP 695
#: 'type PriorityTier = ...' statements produce TypeAliasType, which StandardSchemaAdapter
#: does not unwrap. Standard assignment keeps the annotation as a direct Literal.
PriorityTier = Literal["standard", "premium", "vip"]


@dataclass(slots=True)
class ContactInfo:
    """Guest contact information with explicit required and optional fields.

    In Agnara's StandardSchemaAdapter:
    - ``email: str`` has no default, so it compiles as required in JSON Schema.
    - ``phone: str | None = None`` has a default, compiling as optional (required=False).
    """

    email: str
    phone: str | None = None


@dataclass(slots=True)
class Guest:
    """Composite guest profile demonstrating nested dataclass contracts.

    Nested dataclasses are recursively validated by StandardSchemaAdapter,
    producing nested JSON Schema object definitions with ``additionalProperties: False``.
    """

    name: str
    contact: ContactInfo
    is_corporate: bool = False


@dataclass(slots=True)
class ReservationConfirmation:
    """Canonical domain result emitted upon successful booking confirmation.

    Demonstrates a rich return contract encompassing primitives, enums,
    literals, collections, and union types.
    """

    reservation_id: str
    guest_name: str
    room_type: RoomType
    nights: int
    total_amount: float
    status: ReservationStatus
    priority: PriorityTier
    amenities: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    special_requests: str | None = None
    reference_code: str | int = "GEN-001"
