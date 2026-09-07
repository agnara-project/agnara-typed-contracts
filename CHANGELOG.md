# Changelog

All notable changes to **Agnara Historical Reference Application #006 (`agnara-typed-contracts`)** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-09-06

### Added
- Canonical implementation of **Agnara Historical Reference Application #006 (`agnara-typed-contracts`)**.
- Domain models and types in `domain.py`:
  - `RoomType`, `ReservationStatus`, `BookingChannel` (standard `StrEnum`).
  - `PriorityTier` (`Literal` scalar options).
  - `ContactInfo` and `Guest` (nested dataclasses with required and optional fields).
  - `ReservationConfirmation` (canonical return dataclass).
- Capabilities declared in `reservations.py`:
  - `book_room` (nested dataclasses, enums, literals, collections, bytes, unions).
  - `cancel_reservation` (primitive string, optional reason, `-> None` contract).
  - `calculate_quote` (variadic tuple, primitive float).
  - `lookup_reservation` (union input `str | int`, union return).
- Interactive demonstration in `app.py` covering 5 comprehensive scenarios:
  1. Happy path booking & typed contract execution.
  2. Strict primitive and literal validation failures (`int`, `bool != int`, `Literal`).
  3. Deep nested dataclass & collection error path tracking (`guest.contact.email`, `amenities[1]`).
  4. Machine-readable schema introspection via `describe_app`.
  5. Return contracts analysis and runtime non-enforcement documentation.
- Comprehensive test suite in `tests/` covering:
  - Primitives (`test_primitives.py`).
  - Collections and unsupported sets (`test_collections.py`).
  - Dataclasses, nesting, and cycle detection (`test_models.py`).
  - Enums, literals, and PEP 695 type aliases (`test_enums_literals.py`).
  - Validation errors, paths, and Failure mapping (`test_validation_errors.py`).
  - Return contracts and adapter compilation (`test_return_contracts.py`).
  - Introspection and JSON Schema fidelity (`test_introspection.py`).
- Architecture specification in `ARCHITECTURE.md`.
- Operational manual for AI agents in `AGENTS.md`.
- Developer guide in `docs/contracts_guide.md`.
- Pinned baseline: `agnara==0.1.0a3` on CPython >= 3.14.
- Repository status permanently marked as **Historical / Frozen**.
