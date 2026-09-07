# Architecture — Agnara Typed Capability Contracts

This document specifies the architectural principles, compile-time mechanics, and runtime validation system implemented in **Agnara Historical Reference Application #006 (`agnara-typed-contracts`)**, pinned to **`agnara==0.1.0a3`** on **CPython >= 3.14**.

---

## 1. The Core Philosophy

In traditional application frameworks, type hints serve primarily as documentation or static verification hints (via mypy/pyright), while runtime validation requires separate schema definitions (such as Pydantic models, Marshmallow schemas, or JSON Schema files).

In Agnara, **Python type hints directly constitute the machine-readable capability contract**:

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

This model guarantees:
1. **Zero Duplicate Definitions:** Handlers declare types once using native Python typing.
2. **Zero Framework Pollution:** Domain logic uses standard dataclasses and standard library enums; no base classes are inherited from Agnara.
3. **Transport Neutrality:** The contract is decoupled from HTTP query parameters, JSON-RPC bodies, or event envelopes (ADR 0002, ADR 0003).

---

## 2. The Schema Port & Adapter Separation (ADR 0004)

Agnara separates schema compilation from runtime execution using two structural `Protocol`s in `agnara.schema.port`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             agnara.schema.port                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  SchemaAdapter (Protocol)                                                   │
│    - compile(annotation: Any) -> TypeSchema                                 │
│    - supports(annotation: Any) -> bool                                      │
│    * Executed at startup compilation (ADR 0005). Fails loudly if a type is  │
│      unsupported.                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  TypeSchema (Protocol)                                                      │
│    - validate(value: object) -> Any                                         │
│    - json_schema() -> JsonSchema (Mapping[str, Any])                        │
│    * Executed per invocation. Completely immutable and thread-safe without   │
│      locking under PEP 703 free-threading (PRINCIPLES P5, P6).              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Structural Protocols?
Both `SchemaAdapter` and `TypeSchema` are `typing.Protocol` classes rather than abstract base classes. An adapter implementation does not need to inherit from Agnara. A high-performance bridge (e.g. msgspec or rust-based validators) can satisfy the port structurally without importing the kernel.

### The Default Implementation: `StandardSchemaAdapter`
Agnara 0.1.0a3 ships with `StandardSchemaAdapter` in `agnara.schema.standard`. It depends **exclusively on the Python standard library**:
- No external model dependencies (Pydantic, marshmallow, msgspec).
- Zero code generation or dynamic eval.
- Direct runtime type checking via compiled `frozen_slots_dataclass` schema objects (`PrimitiveSchema`, `ListSchema`, `DataclassSchema`, `EnumSchema`, `LiteralSchema`, `TupleSchema`, `UnionSchema`, `NoneSchema`).

---

## 3. Strictness & Non-Coercion Policy

The schema port allows validation to return a coerced value (e.g. for an HTTP query parameter `"5"` to be parsed as integer `5`). However, **`StandardSchemaAdapter` strictly refuses to coerce**:

### 1. No String-to-Number Coercion
`validate("3")` against `int` raises `ValidationError("expected int, got str")`.
*Rationale:* Transports (such as HTTP adapters) know their own wire format and must convert strings before passing payloads to the execution kernel. A capability invoked directly from Python or another in-process service has no wire format; silently converting `"3"` would mask caller programming bugs.

### 2. `bool` is NOT `int`
In Python, `isinstance(True, int)` evaluates to `True`. `StandardSchemaAdapter` checks `type(value) is int` rather than `isinstance`:
```python
if type(value) is not self.python_type:
    raise ValidationError(f"expected {self.python_type.__name__}, got {type(value).__name__}")
```
Passing `True` or `False` for an `int` parameter raises `ValidationError: expected int, got bool`.

### 3. Dataclasses Require Exact Instances
A `DataclassSchema` validates `type(value) is self.dataclass_type`. Passing a raw `dict` raises `ValidationError: expected <Class>, got dict`.
*Rationale:* Instantiating domain objects from raw wire mappings belongs at the transport ingress boundary. The execution core operates on validated domain instances.

---

## 4. Compilation vs Runtime Execution Boundary

```
+-------------------------------------------------------------------------------+
| PHASE 1: STARTUP COMPILATION (Ahead of Invocation)                            |
+-------------------------------------------------------------------------------+
  app = Agnara("reservations")
  frozen = app.compile()  # Freezes CapabilityRegistry
  plan = ExecutionPlan.compile(frozen["reservations.book_room"], di_registry)
    ├── 1. Filters dependency parameters (injected by DI)
    ├── 2. Filters context parameters (annotated as ExecutionContext)
    ├── 3. Compiles remaining parameters into plan.input_schemas via adapter
    └── 4. Determines plan.required_inputs (parameters without defaults)

+-------------------------------------------------------------------------------+
| PHASE 2: RUNTIME INVOCATION (Per-Request Hot Path)                            |
+-------------------------------------------------------------------------------+
  result = await invoke_result(plan, context)
    ├── 1. Validate payload inputs (_validate_inputs):
    │      a. Reject unexpected keys: payload keys not in input_schemas
    │      b. Reject missing keys: required_inputs not in payload
    │      c. Execute schema.validate(value) for each payload input
    │      d. Wrap any ValidationError with parameter name in path
    ├── 2. Resolve DI dependencies and inject ExecutionContext
    ├── 3. Execute handler(**arguments)
    └── 4. Return Success(value) or canonical Failure
```

---

## 5. Introspection & Schema Export (`describe_app`)

Introspection reflects what was compiled, producing an immutable `AppDescriptor` and `IntrospectionSnapshot`:

- Each input in `plan.input_schemas` is mapped to an `InputDescriptor`:
  - `name: str`: Parameter name.
  - `required: bool`: Whether the parameter lacks a default value.
  - `schema: str`: Deterministic canonical JSON Schema string (`json.dumps(schema.json_schema(), sort_keys=True)`).
- Descriptors contain plain JSON data and string references (`TypeReference`); they do **not** hold handlers, live dependencies, or runtime objects. This guarantees safe publishing to external viewers, MCP agents, and OpenAPI generators.

---

## 6. Return Contracts in Agnara 0.1.0a3

An essential architectural baseline of `agnara==0.1.0a3`:

1. **Input Contract Enforcement:**
   `ExecutionPlan` compiles and strictly validates input arguments. Missing inputs, unexpected inputs, and invalid input types are caught before handler invocation and converted into `Failure(FailureCode.INVALID_INPUT)`.
2. **Runtime Return Non-Enforcement:**
   Neither `invoke()` nor `invoke_result()` validates return values against handler return type annotations at runtime in `0.1.0a3`. If a handler declares `-> int` and returns a `str`, `invoke_result()` returns `Success("string")`.
3. **Introspection Boundary:**
   `CapabilityDescriptor` in `agnara.introspection` defines `inputs: tuple[InputDescriptor, ...]`, but contains **no** `output` or return schema field.
4. **Adapter Capability:**
   `StandardSchemaAdapter().compile(hints["return"])` successfully compiles return type hints (`NoneSchema` for `-> None`, `DataclassSchema` for confirmation objects, `UnionSchema` for result unions) for external consumers and test verification.

---

## 7. Supported vs Unsupported Type Matrix in `0.1.0a3`

| Type Construct | Supported in a3? | Compilation Mechanism | JSON Schema Representation | Runtime Validation Behavior |
|---|---|---|---|---|
| `int`, `str`, `float`, `bool` | Yes | `PrimitiveSchema` | `integer`, `string`, `number`, `boolean` | Strict `type(v) is T`. No coercion. `bool` is rejected for `int`. |
| `bytes` | Yes | `PrimitiveSchema` | `{"type": "string", "format": "binary"}` | Strict `type(v) is bytes`. |
| `None` / `NoneType` | Yes | `NoneSchema` | `{"type": "null"}` | Strict `v is None`. |
| `T \| None` (`Optional[T]`) | Yes | `UnionSchema` | `{"anyOf": [...]}` | Matches if any choice validates. |
| `list[T]` | Yes | `ListSchema` | `{"type": "array", "items": {...}}` | Strict `type(v) is list`. Validates each element with index in path. |
| `dict[str, T]` | Yes | `DictionarySchema` | `{"type": "object", "additionalProperties": {...}}` | Strict `type(v) is dict`. Rejects non-str keys. Validates values. |
| `tuple[T1, T2]` | Yes | `TupleSchema(variadic=False)` | `{"prefixItems": [...], "items": false, "minItems": N, "maxItems": N}` | Strict `type(v) is tuple`. Exact length and item validation. |
| `tuple[T, ...]` | Yes | `TupleSchema(variadic=True)` | `{"type": "array", "items": {...}}` | Strict `type(v) is tuple`. Homogeneous elements. |
| `StrEnum` / `Enum` | Yes | `EnumSchema` | `{"enum": [...], "type": "string"}` | Requires `type(v) is EnumClass`. Does NOT coerce raw strings. |
| `Literal["a", "b"]` | Yes | `LiteralSchema` | `{"enum": ["a", "b"]}` (or `{"const": "a"}`) | Accepts raw scalar values directly from payload. |
| Standard `@dataclass` | Yes | `DataclassSchema` | `{"type": "object", "properties": {...}, "additionalProperties": false}` | Requires `type(v) is Dataclass`. Recursively validates fields. |
| `dict[int, str]` | **No** | Fails at startup: `SchemaError` | N/A | Rejected at compile time (keys must be `str`). |
| `set[T]`, `frozenset[T]` | **No** | Fails at startup: `SchemaError` | N/A | Rejected at compile time (not supported by adapter). |
| Recursive dataclass | **No** | Fails at startup: `SchemaError` | N/A | Cycle detected: `recursive dataclass graph: Node -> Node`. |
| Dataclass with `InitVar` | **No** | Fails at startup: `SchemaError` | N/A | Requires directional schema support. |
| Dataclass with `init=False` | **No** | Fails at startup: `SchemaError` | N/A | Requires directional schema support. |
| `type Alias = ...` (PEP 695) | **No** | Fails at startup: `SchemaError` | N/A | Generates `TypeAliasType` which a3 does not unwrap. Use standard assignment. |
| Pydantic `BaseModel` | **No** | Fails at startup: `SchemaError` | N/A | External dependencies excluded by ADR 0004. |
