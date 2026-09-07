---
name: contract-validation
description: Operational workflow for verifying typed capability contracts, schema compilation, strictness invariants, and introspection against agnara==0.1.0a3.
---

# Contract Validation Skill

Use this skill when auditing, verifying, or testing type contracts, schema compilation, and introspection fidelity in **Agnara Historical Reference Application #006 (`agnara-typed-contracts`)**.

---

## 1. When to Use This Skill

Activate this skill whenever:
- Verifying the dual nature of Python type hints: static checking vs runtime capability contracts.
- Inspecting how `ExecutionPlan.compile` processes parameters and classifies them into DI dependencies, context parameters, and payload `TypeSchema` objects.
- Checking runtime input validation strictness (ensuring no silent coercion occurs: `"3"` fails for `int`, `True` fails for `int`, raw dicts fail for dataclasses).
- Verifying error propagation paths in nested structures (`ValidationError.path` and `.location`).
- Inspecting generated machine-readable JSON Schema representations produced by `describe_app` and `InputDescriptor`.
- Validating the boundary of return contracts (verifying that a3 does not validate returns at runtime and exports inputs only in `CapabilityDescriptor`).

---

## 2. Relevant Inputs

- **`StandardSchemaAdapter`:** The standard library schema compiler protocol implementation.
- **`TypeSchema`:** Compiled runtime schema executing `.validate()` and `.json_schema()`.
- **`ExecutionPlan`:** The compiled capability plan containing `input_schemas` and `required_inputs`.
- **`ExecutionContext` & `Invocation`:** Runtime dispatch request and environment.
- **`describe_app`:** Introspection builder producing `AppDescriptor` and `InputDescriptor`s.

---

## 3. Ordered Implementation Workflow

### Step 1: Baseline & Dependency Check
1. Ensure the Python environment runs CPython >= 3.14.
2. Confirm the installed framework is strictly `agnara==0.1.0a3`:
   ```python
   import agnara

   assert agnara.__version__ == "0.1.0a3"
   ```

### Step 2: Signature & Type Compilation Audit
1. Inspect handler parameter type annotations with `typing.get_type_hints(handler)`.
2. Verify all parameters are positional-or-keyword or keyword-only.
3. Verify that `StandardSchemaAdapter().compile(annotation)` succeeds for supported types:
   - Primitives: `bool`, `int`, `float`, `str`, `bytes`.
   - Nullability & Optionals: `None`, `T | None`.
   - Collections: `list[T]`, `dict[str, T]`, `tuple[...]`.
   - Structures: `@dataclass` instances, `StrEnum`, `Literal[...]`.
4. Ensure unsupported constructs fail fast with `SchemaError`:
   - `dict[int, str]` (non-string keys).
   - `set[T]`, `frozenset[T]`.
   - Recursive dataclasses (`recursive dataclass graph`).
   - Dataclasses with `InitVar` or `init=False`.
   - PEP 695 `type Alias = ...` (produces `TypeAliasType`).
   - Third-party models (e.g. `pydantic.BaseModel`).

### Step 3: Runtime Validation & Non-Coercion Check
1. Test valid inputs to confirm successful execution and `Success[T]` outcome.
2. Test non-coercion boundary:
   - String `"3"` passed for `int` must fail with `ValidationError: expected int, got str`.
   - Boolean `True` passed for `int` must fail with `ValidationError: expected int, got bool`.
   - Raw dictionary passed for a dataclass must fail with `ValidationError: expected <Class>, got dict`.
   - Raw string passed for `StrEnum` must fail with `ValidationError: expected <Enum>, got str`.

### Step 4: Error Path Verification
1. Verify that `ValidationError` captures the complete nested path as a tuple of `str | int`.
2. Confirm that nested errors format location correctly (e.g. `guest.contact.email`, `amenities[1]`).
3. Confirm that `invoke_result()` projects errors into `Failure(FailureCode.INVALID_INPUT, message, details={"path": ...})`.

### Step 5: Introspection & Export Verification
1. Run `describe_app(app, plans.values())`.
2. Verify that each declared input yields an `InputDescriptor` with valid JSON Schema.
3. Verify that `CapabilityDescriptor` has NO `output` or return descriptor (as per `0.1.0a3` public contract).

---

## 4. Operational Boundaries & Negative Constraints

- **Never make a type appear supported by Agnara merely because normal Python execution accepts it.**
- **Do not modernize this repository to match later Agnara typing, validation, schema, or introspection behavior.**
- **Do NOT introduce third-party validation libraries:** Pydantic, marshmallow, or msgspec must remain strictly out of core (ADR 0004).
- **Do NOT claim runtime return validation exists in 0.1.0a3:** Handlers declare return type hints for static analysis and adapter compilation, but the a3 runtime does not validate return values.

---

## 5. Validations & Definition of Done

The contract validation workflow is complete when:
- [ ] `pytest -v` runs all 36 tests with zero failures.
- [ ] `python app.py` completes all 5 scenarios with exit code `0`.
- [ ] All 4 layers (Python annotation, Agnara introspection, Agnara validation, machine-readable contract) are clearly distinguished in documentation and tests.
- [ ] The support matrix in `README.md` and `ARCHITECTURE.md` accurately reflects verified a3 behavior.
