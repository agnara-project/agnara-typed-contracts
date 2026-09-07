# Developer Guide — Typed Capability Contracts in Agnara 0.1.0a3

This guide details best practices and practical patterns for authoring capability contracts in **`agnara==0.1.0a3`**.

---

## 1. Designing Stable Capability Contracts

When declaring a capability with `@app.capability`, every parameter signature is evaluated during startup compilation (`ExecutionPlan.compile`).

### Rule 1: Every Input Parameter Must Have a Type Annotation
In Agnara, untyped parameters raise `DefinitionError` during plan compilation:
```python
# INVALID: Raises DefinitionError
@app.capability()
def bad_handler(nights): ...


# VALID: Compiled to PrimitiveSchema(int)
@app.capability()
def good_handler(nights: int): ...
```

### Rule 2: Use Positional-or-Keyword or Keyword-Only Parameters
Variable arguments (`*args`, `**kwargs`) and positional-only arguments (`/`) are rejected by `ExecutionPlan` with `DefinitionError`:
```python
# INVALID: Raises DefinitionError
@app.capability()
def var_args_handler(*items: str): ...


# VALID: Fixed or variadic tuple
@app.capability()
def tuple_handler(items: tuple[str, ...]): ...
```

---

## 2. Choosing Between `Enum` and `Literal`

Both `Enum` (such as `StrEnum`) and `Literal[...]` allow restricting inputs to a closed set of choices. However, they behave differently in raw payloads:

| Characteristic | `Enum` (`StrEnum`) | `Literal["a", "b"]` |
|---|---|---|
| **Python Type** | Subclass of `enum.Enum` | `typing.Literal` generic alias |
| **JSON Schema** | `{"enum": [...], "type": "string"}` | `{"enum": [...]}` |
| **In-Process Python Payload** | Requires `MyEnum.CHOICE` instance | Accepts `"choice"` string directly |
| **Transport Ingress Parsing** | Wire adapter must instantiate `MyEnum` | Wire adapter passes string through |

### Recommendation:
- Use `Literal[...]` when authoring capabilities intended for direct remote invocation where payload parameters arrive as plain JSON dictionaries.
- Use `StrEnum` when domain entities or internal business logic benefit from Python enum member identity and method encapsulation.

---

## 3. Modeling Complex Inputs with Dataclasses

Agnara 0.1.0a3 natively compiles standard library `@dataclass` classes:
```python
from dataclasses import dataclass


@dataclass(slots=True)
class ContactInfo:
    email: str  # Compiled as required: true
    phone: str | None = None  # Compiled as required: false
```

### Key Considerations:
1. **No External Dependencies:** Do not use `pydantic.BaseModel` in capability signatures; `StandardSchemaAdapter` rejects classes that are not standard dataclasses.
2. **Strict Instance Checking:** Callers invoking the capability in Python must construct domain dataclass instances. The runtime does not deserialize raw dictionaries into dataclasses.
3. **Avoid Recursive Models:** Agnara rejects self-referencing dataclasses (`recursive dataclass graph`) during startup compilation.
4. **Avoid `InitVar` and `init=False`:** Fields using `InitVar` or `field(init=False)` fail compilation in `0.1.0a3` because directional schema mapping is not supported.

---

## 4. Understanding Error Propagation

When validation fails, Agnara raises a `ValidationError` containing the structured path to the invalid element:
- Top-level field: `path=("nights",)` $\rightarrow$ `"nights: expected int, got str"`
- Collection item: `path=("amenities", 1)` $\rightarrow$ `"amenities[1]: expected str, got int"`
- Nested dataclass field: `path=("guest", "contact", "email")` $\rightarrow$ `"guest.contact.email: expected str, got int"`

When invoked via `invoke_result()`, this error is canonicalized into:
```python
Failure(
    code=FailureCode.INVALID_INPUT,
    message="expected str, got int",
    details={"path": ("guest", "contact", "email")},
)
```
Transport adapters (such as HTTP or MCP) map this canonical failure directly into their protocol-specific error representations.
