# Agnara Historical Reference Application #006: `agnara-typed-contracts`

[![Agnara Version](https://img.shields.io/badge/agnara-0.1.0a3-blue.svg)](https://pypi.org/project/agnara/0.1.0a3/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.14-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Historical%20%2F%20Frozen-lightgrey.svg)](#frozen-status)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

> **The canonical reference application demonstrating the philosophy: `Python types → machine-readable capability contract`.**
> Explains type introspection, strict validation, schema extraction, and framework boundaries using **`agnara==0.1.0a3`** on **CPython >= 3.14**.

---

## 1. Mission & Conceptual Flow

In traditional frameworks, type hints are purely advisory or require external schema libraries (such as Pydantic, Marshmallow, or JSON Schema files) that pollute domain code with framework-specific base classes and dynamic metaclasses.

In Agnara, **native Python type annotations directly define the capability contract**:

```
      Python Handler Signature
   def book_room(guest: Guest, nights: int, ...) -> ReservationConfirmation:
                      │
                      ▼  Startup Compilation (ExecutionPlan.compile)
          StandardSchemaAdapter.compile()
                      │
                      ▼
             Immutable TypeSchema
         ┌──────────────────────────────┐
         │ 1. Runtime Validation Engine │ ──> Enforces payload types on invocation
         │ 2. JSON Schema Producer      │ ──> Generates OpenAPI / MCP / Tool specs
         └──────────────────────────────┘
                      │
                      ▼  Introspection (describe_app)
            InputDescriptor.schema
```

1. **Dual Role of Type Hints:**
   - **Static Verification:** Standard type checkers (`mypy`, `pyright`) verify call sites at authoring time.
   - **Machine-Readable Capability Contract:** At startup (`ExecutionPlan.compile`), Agnara compiles every parameter type hint into an immutable, thread-safe `TypeSchema`.
2. **Standard Library Purity (ADR 0004):**
   - Core Agnara depends on **zero external modeling libraries**.
   - Standard library primitives, `@dataclass` classes, `StrEnum` enumerations, and `typing.Literal` form the entire modeling surface.
3. **Strict Non-Coercing Boundary:**
   - Agnara does **not** silently coerce types (e.g. string `"3"` is rejected for `int`).
   - `bool` is strictly rejected where `int` is declared (`isinstance(True, int)` is prevented).
   - Domain dataclasses require exact instances; wire parsing belongs at transport boundaries.

---

## 2. The Four Distinct Contract Layers

To understand typed capability contracts in Agnara 0.1.0a3, one must distinguish four separate conceptual layers:

```
+─────────────────────────────────────────────────────────────────────────────+
|                         THE FOUR CONTRACT LAYERS                            |
+─────────────────────────────────────────────────────────────────────────────+

  1. PYTHON ANNOTATION (Authoring Surface)
     What the Python source code declares:
     nights: int, stay_dates: tuple[str, str], guest: Guest

  2. AGNARA INTROSPECTION (Inspection Surface)
     What Agnara inspects at startup and records in AppDescriptor:
     InputDescriptor(name="nights", required=True, schema=...)

  3. AGNARA VALIDATION (Runtime Kernel)
     What Agnara actually validates on the invocation hot path:
     _validate_inputs() calls TypeSchema.validate(value)
     - Strict exact type checking (type(v) is int)
     - Preserves nested error path: ('guest', 'contact', 'email')

  4. MACHINE-READABLE CONTRACT (Published Data Format)
     The protocol-neutral JSON Schema document fragment exported:
     {"type": "integer"}, {"type": "object", "properties": {...}}
     Consumed by OpenAPI generators, MCP agent discovery, and CLIs.
```

If a feature is present in Python annotations but not validated or exported by Agnara in `0.1.0a3`, this reference application documents that exact boundary rather than simulating non-existent framework mechanics.

---

## 3. What This Application Teaches

1. **How Type Hints Form Part of the Contract:**
   - Why every input parameter in a capability handler requires an explicit type hint.
   - How `ExecutionPlan.compile` inspects signatures and maps types to `TypeSchema` objects.
2. **What Agnara Can Inspect (`describe_app`):**
   - How `describe_app()` traverses compiled execution plans to build an `AppDescriptor` and `IntrospectionSnapshot`.
   - How Python types project into standard JSON Schema documents inside `InputDescriptor` for OpenAPI and MCP discovery.
3. **How Validation Errors Appear:**
   - How `ValidationError` tracks exact nested failure paths (`guest.contact.email`, `amenities[1]`).
   - How `invoke_result()` canonicalizes input validation failures into `Failure(code=FailureCode.INVALID_INPUT, message=..., details={"path": ...})`.
4. **How to Design Clear, Stable Contracts:**
   - Choosing between `StrEnum` (domain identity) and `Literal` (direct wire payload choices).
   - Modeling nested structures with `@dataclass` and determining required vs optional fields via field defaults.
5. **Real Boundaries of `agnara==0.1.0a3`:**
   - What `StandardSchemaAdapter` supports vs what fails compilation (such as `dict[int, str]`, `set`, and recursive dataclasses).
   - Why `0.1.0a3` enforces input contracts on invocation while leaving return validation and output descriptors to domain adapters.

---

## 4. Historical Baseline & Version Pinning

| Dimension | Specification |
|---|---|
| **Framework Version** | Strictly pinned to **`agnara==0.1.0a3`** |
| **Python Runtime** | **CPython >= 3.14** (tested on CPython 3.14.4 under PEP 703 free-threading semantics) |
| **Repository Status** | **Historical / Frozen** |
| **Public API Scope** | Exclusively uses real exports from `0.1.0a3`; no speculative or post-a3 APIs |

<a id="frozen-status"></a>
> [!WARNING]
> **Historical / Frozen Baseline:**
> This repository is **Agnara Historical Reference Application #006**, intentionally bound to **`agnara==0.1.0a3`** on **CPython >= 3.14** and must **not** be modernized to newer Agnara typing, validation, schema, or contract APIs. It preserves the exact type contract semantics, schema compilation rules, and validation behavior of that release.

---

## 5. Support Matrix: Type Contracts in `0.1.0a3`

The following matrix records the verified status of all evaluated type constructs in `agnara==0.1.0a3`:

| Contract Feature | a3 Status | Demonstrated in #006 | Implementation & Notes |
|---|---|---|---|
| **Primitive Types (`int`, `str`, `float`, `bool`, `bytes`)** | **Publicly Supported** | Yes (`book_room`) | Handled via `PrimitiveSchema`. Strict type matching without coercion. `bool` is rejected for `int`. |
| **Nullability (`None`, `NoneType`)** | **Publicly Supported** | Yes (`cancel_reservation`) | Handled via `NoneSchema`. Maps to JSON Schema `{"type": "null"}`. |
| **Optional Values (`T \| None`, `Optional[T]`)** | **Publicly Supported** | Yes (`special_requests`) | Handled via `UnionSchema`. Maps to JSON Schema `{"anyOf": [...]}`. |
| **Homogeneous Lists (`list[T]`)** | **Publicly Supported** | Yes (`amenities`) | Handled via `ListSchema`. Maps to `{"type": "array", "items": {...}}`. Element index tracked in path. |
| **String-Keyed Dictionaries (`dict[str, T]`)** | **Publicly Supported** | Yes (`metadata`) | Handled via `DictionarySchema`. Maps to `{"type": "object", "additionalProperties": {...}}`. |
| **Fixed-Length Tuples (`tuple[T1, T2]`)** | **Publicly Supported** | Yes (`stay_dates`) | Handled via `TupleSchema`. Maps to `prefixItems` with `minItems`/`maxItems`. |
| **Variadic Tuples (`tuple[T, ...]`)** | **Publicly Supported** | Yes (`calculate_quote`) | Handled via `TupleSchema(variadic=True)`. Maps to `items`. |
| **Enums (`StrEnum`, `Enum`)** | **Publicly Supported** | Yes (`room_type`) | Handled via `EnumSchema`. Requires exact Enum member instance in Python payload. |
| **Literals (`Literal[...]`)** | **Publicly Supported** | Yes (`priority`) | Handled via `LiteralSchema`. Accepts raw scalar strings directly from payload. |
| **Standard Dataclasses (`@dataclass`)** | **Publicly Supported** | Yes (`guest: Guest`) | Handled via `DataclassSchema`. Recursive field validation and path tracking. Defaults determine `required`. |
| **Non-String Dict Keys (`dict[int, str]`)** | **Not Supported** | Yes (`test_collections.py`) | Fails at startup: `SchemaError: dictionary keys must be str`. |
| **Sets (`set[T]`, `frozenset[T]`)** | **Not Supported** | Yes (`test_collections.py`) | Fails at startup: `SchemaError: set is not supported by StandardSchemaAdapter`. |
| **PEP 695 Type Aliases (`type Foo = ...`)** | **Not Supported** | Yes (`test_enums_literals.py`)| Fails at startup: `SchemaError` (produces `TypeAliasType` which a3 does not unwrap). |
| **Recursive Dataclasses** | **Not Supported** | Yes (`test_models.py`) | Fails at startup: `SchemaError: recursive dataclass graph: Node -> Node`. |
| **Dataclass `InitVar` / `init=False`** | **Not Supported** | Yes (`test_models.py`) | Fails at startup: `SchemaError: ... requires directional schema support`. |
| **Third-Party Models (`pydantic.BaseModel`)**| **Not Supported** | Yes (`test_models.py`) | Fails at startup: `SchemaError` (ADR 0004 keeps external models out of core). |
| **Runtime Return Value Enforcement** | **Not Supported** | Yes (`test_return_contracts.py`)| Handlers declare return hints, but `invoke_result()` does not validate returns at runtime. |
| **Introspection Output Descriptors** | **Not Supported** | Yes (`test_introspection.py`) | `CapabilityDescriptor` defines `inputs` only; no output schema descriptor in a3. |

---

## 6. Quick Start (Under 2 Minutes)

### Prerequisites
- **CPython >= 3.14**
- **PowerShell**, **Bash**, or **Zsh**

### Reproduction Steps

```powershell
# 1. Clone repository
git clone https://github.com/agnara-project/agnara-typed-contracts.git
cd agnara-typed-contracts

# 2. Create virtual environment with Python 3.14
py -3.14 -m venv .venv

# 3. Activate the virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux / macOS:
# source .venv/bin/activate

# 4. Install pinned requirements and dev dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# 5. Verify exact version dynamically
python -c "import agnara; assert agnara.__version__ == '0.1.0a3', f'Wrong version: {agnara.__version__}'"

# 6. Run the interactive demonstration script
python app.py

# 7. Run the complete test suite (36 tests)
pytest -v

# 8. Verify style and formatting
ruff check .
ruff format --check .
```

---

## 7. Domain Walkthrough: The Reservation System

This reference application implements a hotel and event reservation system with 4 capabilities:

```
reservations
├── book_room             (risk=MEDIUM, effects=[DATABASE_WRITE])
├── cancel_reservation    (risk=MEDIUM, effects=[DATABASE_WRITE], idempotent=True)
├── calculate_quote       (risk=LOW,    effects=[READ],           idempotent=True)
└── lookup_reservation    (risk=LOW,    effects=[READ],           idempotent=True)
```

### Signature Analysis of `book_room`:
```python
@app.capability(
    name="book_room",
    risk=Risk.MEDIUM,
    effects=[StandardEffect.DATABASE_WRITE],
)
def book_room(
    guest: Guest,                         # Nested Dataclass (Guest -> ContactInfo)
    room_type: RoomType,                  # StrEnum ("single", "double", "suite", "deluxe")
    stay_dates: tuple[str, str],          # Fixed-length tuple (check-in, check-out)
    nights: int,                          # Strict integer (rejects "3" and True)
    nightly_rate: float,                  # Strict float
    priority: PriorityTier,               # Literal["standard", "premium", "vip"]
    amenities: list[str],                 # Homogeneous list of strings
    metadata: dict[str, str],             # String-keyed homogeneous dictionary
    special_requests: str | None = None,  # Optional string (default None -> required=False)
    deposit_token: bytes | None = None,   # Optional bytes (format: binary)
    reference_code: str | int = "AUTO",   # Union type with default
) -> ReservationConfirmation:             # Return contract (Dataclass)
```

---

## 8. Deep Dive: The Five Interactive Scenarios (`python app.py`)

Running `python app.py` executes 5 comprehensive pedagogical scenarios:

### Scenario 1: Happy Path Booking & Contract Assembly
Dispatches a valid, fully typed payload via `invoke_result()`, verifying the canonical `Success(ReservationConfirmation)` output. Demonstrates how Python domain objects flow seamlessly into capability handlers.

### Scenario 2: Strict Primitive & Literal Validation Failures
Demonstrates that Agnara strictly enforces exact types without coercion:
- Passing string `"3"` for `nights: int` $\rightarrow$ `Failure(INVALID_INPUT, "expected int, got str", path=('nights',))`
- Passing boolean `True` for `nights: int` $\rightarrow$ `Failure(INVALID_INPUT, "expected int, got bool", path=('nights',))` (prevents Python `bool/int` confusion).
- Passing `"ultra-vip"` for `priority: PriorityTier` $\rightarrow$ `Failure(INVALID_INPUT, "expected one of ('standard', 'premium', 'vip'), got 'ultra-vip'", path=('priority',))`

### Scenario 3: Deep Nested Dataclass & Collection Path Tracking
Demonstrates structured path reporting when failures occur inside nested hierarchies:
- Invalid item in `amenities: list[str]` (index 1 is `404`) $\rightarrow$ Path: `('amenities', 1)`, formatted as `amenities[1]: expected str, got int`.
- Invalid field in nested dataclass `guest.contact.email` (`99999`) $\rightarrow$ Path: `('guest', 'contact', 'email')`, formatted as `guest.contact.email: expected str, got int`.

### Scenario 4: Machine-Readable Schema Introspection (`describe_app`)
Runs `describe_app(app, plans.values())` and demonstrates how Python type hints generate protocol-neutral JSON Schema documents for each capability input (`InputDescriptor.schema`).

### Scenario 5: Return Contracts & Framework Boundary Analysis
Inspects return type annotations (`-> ReservationConfirmation`, `-> None`, `-> float`, `-> ReservationConfirmation | None`), demonstrates compilation via `StandardSchemaAdapter`, and explains why Agnara `0.1.0a3` validates inputs strictly at runtime while leaving return validation and output descriptors to domain adapters.

---

## 9. Public APIs of `agnara==0.1.0a3` Utilized

1. **Kernel & Authoring:**
   - `Agnara`: Root authoring application surface (`app = Agnara("reservations")`).
   - `Risk`: Capability risk classification enum (`Risk.LOW`, `Risk.MEDIUM`).
   - `CapabilityId`: Strongly-typed capability identifier (`CapabilityId.parse(...)`).
   - `StandardEffect`: Canonical side-effect declarations (`DATABASE_WRITE`, `READ`).
2. **Schema Subsystem (`agnara.schema`):**
   - `SchemaAdapter`, `TypeSchema`, `JsonSchema`: The schema port protocols.
   - `StandardSchemaAdapter`: The standard library schema compiler.
   - `PrimitiveSchema`, `NoneSchema`, `ListSchema`, `DictionarySchema`, `TupleSchema`, `DataclassSchema`, `EnumSchema`, `LiteralSchema`, `UnionSchema`: Immutable compiled schema classes.
3. **Error Reporting:**
   - `SchemaError`: Compile-time failure on unsupported type annotations.
   - `ValidationError`: Runtime validation failure with structured `path` tuple and `.location` property.
4. **Execution Runtime (`agnara.execution`):**
   - `ExecutionPlan`: Compiled capability execution plan containing `input_schemas` and `required_inputs`.
   - `ExecutionContext`: Isolated runtime execution environment holding `Invocation` and `DIContainer`.
   - `Invocation`: Protocol-neutral request envelope.
   - `invoke`, `invoke_result`: Capability runners.
   - `Success`, `Failure`, `FailureCode`: Canonical execution outcome types.
5. **Introspection Engine (`agnara.introspection`):**
   - `describe_app`: Builds `AppDescriptor` and `IntrospectionSnapshot`.
   - `AppDescriptor`, `CapabilityDescriptor`, `InputDescriptor`: Machine-readable descriptor tree.

---

## 10. Negative Evidence: Unsupported & Excluded Features

The following features were investigated against the published distribution of `agnara==0.1.0a3` and confirmed to be **unsupported**:

1. **No Non-String Dict Keys:** `dict[int, str]` raises `SchemaError: dictionary keys must be str`.
2. **No Set Validation:** `set[T]` and `frozenset[T]` raise `SchemaError: set is not supported by StandardSchemaAdapter`.
3. **No PEP 695 Type Aliases:** `type PriorityTier = Literal[...]` produces `TypeAliasType` which `StandardSchemaAdapter` does not unwrap. Standard assignment (`PriorityTier = Literal[...]`) must be used.
4. **No Third-Party Models in Core:** Classes that are not dataclasses (e.g. `pydantic.BaseModel`) fail compilation (ADR 0004).
5. **No Recursive Dataclasses:** Self-referencing models raise `SchemaError: recursive dataclass graph: Node -> Node`.
6. **No Dataclass `InitVar` or `init=False`:** Fields with `InitVar` or `field(init=False)` fail with `SchemaError: ... requires directional schema support`.
7. **No Implicit Type Coercion:** Passing `"3"` for `int` fails; passing `True` for `int` fails; passing a `dict` for a `@dataclass` fails.
8. **No Runtime Return Validation:** `ExecutionPlan` only compiles inputs; `invoke_result()` does not validate handler return values at runtime in `0.1.0a3`.
9. **No Introspection Output Descriptors:** `CapabilityDescriptor` only provides `inputs: tuple[InputDescriptor, ...]`; no output schema descriptor exists in `0.1.0a3`.

---

## 11. Verification Results & Test Evidence

All 36 tests pass cleanly on CPython 3.14.4 under `agnara==0.1.0a3`:

```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
rootdir: agnara-typed-contracts, configfile: pyproject.toml
testpaths: tests
collected 36 items

tests/test_collections.py::test_homogeneous_list_schema PASSED           [  2%]
tests/test_collections.py::test_string_keyed_dictionary_schema PASSED    [  5%]
tests/test_collections.py::test_fixed_length_tuple_schema PASSED         [  8%]
tests/test_collections.py::test_variadic_tuple_schema PASSED             [ 11%]
tests/test_collections.py::test_unsupported_collections_fail_at_compile_time PASSED [ 13%]
tests/test_enums_literals.py::test_strenum_contract_and_validation PASSED [ 16%]
tests/test_enums_literals.py::test_literal_contract_and_validation PASSED [ 19%]
tests/test_enums_literals.py::test_single_literal_produces_const_schema PASSED [ 22%]
tests/test_enums_literals.py::test_unsupported_literal_and_enum_constructs PASSED [ 25%]
tests/test_enums_literals.py::test_pep695_type_alias_is_unsupported_in_a3 PASSED [ 27%]
tests/test_introspection.py::test_describe_app_generates_valid_descriptors PASSED [ 30%]
tests/test_introspection.py::test_input_descriptors_and_json_schema_fidelity PASSED [ 33%]
tests/test_introspection.py::test_capability_descriptor_has_no_output_descriptor_in_a3 PASSED [ 36%]
tests/test_introspection.py::test_app_descriptor_json_serialization PASSED [ 38%]
tests/test_models.py::test_dataclass_exact_instance_requirement PASSED   [ 41%]
tests/test_models.py::test_dataclass_json_schema_required_fields PASSED  [ 44%]
tests/test_models.py::test_nested_dataclass_validation_and_path_reporting PASSED [ 47%]
tests/test_models.py::test_unsupported_recursive_dataclass_fails_at_compile_time PASSED [ 50%]
tests/test_models.py::test_unsupported_init_var_fails_at_compile_time PASSED [ 52%]
tests/test_models.py::test_unsupported_init_false_fails_at_compile_time PASSED [ 55%]
tests/test_models.py::test_unsupported_third_party_models_fail_at_compile_time PASSED [ 58%]
tests/test_primitives.py::test_primitive_types_are_supported PASSED      [ 61%]
tests/test_primitives.py::test_primitive_validation_strictness_no_coercion PASSED [ 63%]
tests/test_primitives.py::test_bool_is_not_int PASSED                    [ 66%]
tests/test_primitives.py::test_int_is_not_float PASSED                   [ 69%]
tests/test_primitives.py::test_bytes_primitive_schema PASSED             [ 72%]
tests/test_primitives.py::test_none_primitive_schema PASSED              [ 75%]
tests/test_return_contracts.py::test_return_type_hints_can_be_compiled_by_adapter PASSED [ 77%]
tests/test_return_contracts.py::test_execution_plan_does_not_hold_return_schema_in_a3 PASSED [ 80%]
tests/test_return_contracts.py::test_runtime_does_not_enforce_return_types_in_a3 PASSED [ 83%]
tests/test_validation_errors.py::test_missing_required_input_fails PASSED [ 86%]
tests/test_validation_errors.py::test_unexpected_input_fails PASSED      [ 88%]
tests/test_validation_errors.py::test_primitive_type_mismatch_fails PASSED [ 91%]
tests/test_validation_errors.py::test_collection_index_error_path PASSED [ 94%]
tests/test_validation_errors.py::test_nested_dataclass_error_path PASSED [ 97%]
tests/test_validation_errors.py::test_validation_error_formatting PASSED [100%]

============================= 36 passed in 0.17s ==============================
```

---

## 12. License

This repository is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.