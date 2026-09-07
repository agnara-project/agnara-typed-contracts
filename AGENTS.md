# AGENTS.md — Operational Manual for Autonomous AI Agents

> **Audience:** Claude Code, OpenAI Codex, Antigravity, and other autonomous AI coding agents inspecting, maintaining, or extending this codebase.
> **Role:** Single source of operational truth for machine agents. For human-oriented documentation, see `README.md`.

---

## 1. Project Identity & Historical Context

- **Repository:** `agnara-project/agnara-typed-contracts`
- **Designation:** **Agnara Historical Reference Application #006**
- **Framework Version:** Strictly pinned to **`agnara==0.1.0a3`**
- **Python Version:** **CPython >= 3.14** (designed for free-threaded compatibility under PEP 703)
- **Status:** **Historical / Frozen**
- **Mission:** Demonstrate the philosophy `Python types → machine-readable capability contract` using exclusively the real public capabilities and internal mechanics of `agnara==0.1.0a3`.

---

## 2. Inviolable Architectural Invariants

1. **Do Not Upgrade Agnara:** Under no circumstances should `pyproject.toml` or `requirements.txt` be altered to reference versions later than `0.1.0a3` or unreleased development branches (`main`/`develop`).
2. **Do Not Invent Speculative APIs:** Use only the real public API surface present in `agnara==0.1.0a3`. Do not assume schema generation or introspection capabilities exist if they are not part of `0.1.0a3`.
3. **Never Make a Type Appear Supported Merely Because Normal Python Accepts It:**
   - Python dataclasses allow assigning mismatched types dynamically at runtime. Agnara's `DataclassSchema` explicitly validates each field recursively.
   - Python's `isinstance(True, int)` is `True`. Agnara's `PrimitiveSchema(int)` rejects `bool` explicitly.
   - Do not claim or configure Agnara to support types (e.g. `set[T]`, `dict[int, str]`, recursive models) that `StandardSchemaAdapter` rejects at compile time.
4. **Do Not Modernize to Match Later Agnara Behavior:**
   - Future Agnara versions may introduce runtime return validation, directional schemas, or output introspection descriptors. **Do NOT backport or simulate those features here.**
   - Preserve the exact behavior of `0.1.0a3`, where return types are not validated by the execution engine and `CapabilityDescriptor` only provides `inputs`.
5. **Strict Non-Coercion Policy:** `StandardSchemaAdapter` does **not** coerce types. Passing `"3"` for `int` fails. Passing a `dict` where a `@dataclass` is expected fails. Wire format parsing belongs at transport boundaries, not in the core kernel.
6. **No Third-Party Models in Core:** Dataclasses and standard library `StrEnum` are the supported schema models. Do not introduce Pydantic or external schema libraries into core capabilities (ADR 0004).
7. **No PEP 695 `type Alias = ...` in Signatures:** In Python 3.12+, the `type` statement produces a `TypeAliasType` which `StandardSchemaAdapter` in `0.1.0a3` does not unwrap. Use standard assignment (`Alias = Literal[...]`).
8. **Preserve CPython 3.14+ Compatibility:** Maintain strict compatibility with modern Python 3.14+ idioms and free-threaded execution semantics (lock-free reads on frozen objects).

---

## 3. The Four Distinct Contract Layers

Agents inspecting or modifying this repository must maintain a rigorous distinction between these 4 levels:

1. **Python Annotation:** What is declared in Python handler signatures (e.g. `stay_dates: tuple[str, str]`, `guest: Guest`).
2. **Agnara Introspection:** What Agnara inspects and stores in descriptors via `describe_app()` (names, required flags, JSON Schema strings).
3. **Agnara Validation:** What Agnara's compiled `TypeSchema` checks during `_validate_inputs()` at runtime.
4. **Machine-Readable Contract:** The public JSON Schema emitted in `InputDescriptor.schema` for remote agents, OpenAPI, and MCP tools.

---

## 4. Codebase Structure & Ownership

```
agnara-typed-contracts/
├── .agents/
│   ├── AGENTS.md                               # Agent registry metadata
│   └── skills/                                 # Specialized agent workflows
│       ├── contract-validation/SKILL.md        # Type contract verification workflow
│       ├── documentation/SKILL.md              # Documentation sync and quality gates
│       └── testing/SKILL.md                    # Quality gates and negative evidence rules
├── .github/                                    # GitHub repository automation & templates
│   ├── ISSUE_TEMPLATE/                         # Bug report and doc improvement forms
│   ├── PULL_REQUEST_TEMPLATE.md                # Pull request validation checklist
│   ├── dependabot.yml                          # Dependabot configuration ignoring agnara
│   └── workflows/ci.yml                        # CI workflow (CPython 3.14 on Ubuntu & Windows)
├── docs/                                       # Architectural & developer guides
│   └── contracts_guide.md                      # Practical guide to typed contracts in a3
├── tests/                                      # Comprehensive historical test suite (36 tests)
│   ├── __init__.py
│   ├── test_primitives.py                      # Strict primitive validation & bool!=int checks
│   ├── test_collections.py                     # list[T], dict[str, T], tuple[...], and unsupported sets
│   ├── test_models.py                          # Dataclass instances, nesting, defaults, and cycle detection
│   ├── test_enums_literals.py                  # StrEnum vs Literal, JSON Schema, and TypeAliasType tests
│   ├── test_validation_errors.py               # Missing/unexpected inputs, path tuples, and Failure mapping
│   ├── test_return_contracts.py                # Return type hints, adapter compilation, and runtime non-enforcement
│   └── test_introspection.py                   # describe_app, InputDescriptors, and JSON Schema fidelity
├── domain.py                                   # Dataclasses, StrEnums, Literals for reservation system
├── reservations.py                             # Agnara capability declarations & execution plan compiler
├── app.py                                      # Interactive CLI runner demonstrating all 5 contract scenarios
├── pyproject.toml                              # Hatchling build configuration & dev dependencies
├── requirements.txt                            # Exact pinned core dependency (agnara==0.1.0a3)
├── LICENSE                                     # Apache 2.0 License
├── README.md                                   # Comprehensive historical reference documentation
├── ARCHITECTURE.md                             # Deep architectural breakdown of type contracts pipeline
├── CHANGELOG.md                                # Historical release notes
├── CONTRIBUTING.md                             # Frozen repo contribution guidelines
└── SECURITY.md                                 # Security boundary and input validation shielding
```

---

## 5. What May and May Not Be Modified

### Permitted Modifications (Post-Review Maintenance Only)
- Correcting factual errors in documentation or comments.
- Fixing test assertions if upstream CPython 3.14 minor updates change standard library exception messages.
- Enhancing agent skills in `.agents/skills/`.

### Forbidden Modifications
- Changing `agnara==0.1.0a3` to any other version or branch.
- Modifying handler signatures to introduce Pydantic or external schema bridges.
- Changing `StandardSchemaAdapter` non-coercing behavior.
- Adding return contract enforcement or mocking return schemas in `ExecutionPlan`.

---

## 6. Reproducible Command Palette

Agents performing modifications, health checks, or code reviews must run commands using the local virtual environment:

```powershell
# 1. Clean Environment Initialization
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Dependency Installation
pip install -r requirements.txt
pip install -e ".[dev]"

# 3. Dynamic Version Assertion
python -c "import agnara; assert agnara.__version__ == '0.1.0a3', f'Wrong version: {agnara.__version__}'"

# 4. Interactive CLI Demonstration
python app.py

# 5. Comprehensive Test Suite (36 tests)
pytest -v

# 6. Code Style & Formatting Verification
ruff check .
ruff format --check .

# 7. Packaging Verification
pip wheel . --no-deps -w dist
Remove-Item -Recurse -Force dist
```

All verification commands (`pytest -v`, `ruff check .`, `ruff format --check .`, `python app.py`, `pip wheel`) must exit with return code `0`.

---

## 7. Decision Log: Public API Scope vs Excluded Concepts

| Concept | Status in `0.1.0a3` | Decision & Reference Invariant |
|---|---|---|
| **Primitives (`int`, `str`, `float`, `bool`, `bytes`)** | Publicly supported | Handled via `PrimitiveSchema`. Strict type matching without coercion. |
| **Optional / Nullability (`T \| None`, `None`)** | Publicly supported | Handled via `UnionSchema` and `NoneSchema`. |
| **Homogeneous Collections (`list[T]`, `dict[str, T]`, `tuple[...]`)** | Publicly supported | Handled via `ListSchema`, `DictionarySchema`, `TupleSchema`. |
| **Non-String Dict Keys (`dict[int, str]`)** | **Unsupported** | Rejected at compile time (`SchemaError: dictionary keys must be str`). |
| **Sets (`set[T]`, `frozenset[T]`)** | **Unsupported** | Rejected at compile time (`SchemaError: set is not supported`). |
| **Standard Dataclasses (`@dataclass`)** | Publicly supported | Validates exact instance via `DataclassSchema`. Recursive paths tracked. |
| **Recursive Dataclasses** | **Unsupported** | Rejected at compile time (`SchemaError: recursive dataclass graph`). |
| **Dataclass with `InitVar` / `init=False`** | **Unsupported** | Rejected at compile time (`requires directional schema support`). |
| **Enums (`StrEnum`, `Enum`)** | Publicly supported | Handled via `EnumSchema`. Requires exact Enum member instance. |
| **Literals (`Literal[...]`)** | Publicly supported | Handled via `LiteralSchema`. Validates raw scalar string/int/bool choices. |
| **PEP 695 `type Alias = ...`** | **Unsupported** | Rejected at compile time (`TypeAliasType` not unwrapped). Use assignment. |
| **Runtime Return Contract Enforcement** | **Unsupported** | `ExecutionPlan` only compiles inputs; `invoke_result` wraps raw return. |
| **Introspection Output Descriptors** | **Unsupported** | `CapabilityDescriptor` only provides `inputs: tuple[InputDescriptor, ...]`. |
