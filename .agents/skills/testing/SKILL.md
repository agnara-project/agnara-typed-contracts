---
name: testing
description: Testing standards, quality gates, and negative evidence verification for Agnara typed capability contracts.
---

# Testing Skill

Use this skill when authoring, modifying, or executing tests in **Agnara Historical Reference Application #006 (`agnara-typed-contracts`)**.

---

## 1. When to Use This Skill

Activate this skill whenever:
- Adding or modifying unit tests in `tests/`.
- Verifying contract compilation, runtime validation, or introspection behavior.
- Adding negative evidence tests verifying compile-time rejection of unsupported types.
- Running the complete test suite or linting quality gates.

---

## 2. Relevant Inputs

- **`tests/test_primitives.py`:** Tests for primitive validation and non-coercion.
- **`tests/test_collections.py`:** Tests for lists, dicts, tuples, and unsupported collections.
- **`tests/test_models.py`:** Tests for dataclass validation, nesting, and cycle detection.
- **`tests/test_enums_literals.py`:** Tests for enums, literals, and PEP 695 aliases.
- **`tests/test_validation_errors.py`:** Tests for missing/unexpected inputs and error paths.
- **`tests/test_return_contracts.py`:** Tests for return type hints and runtime non-enforcement.
- **`tests/test_introspection.py`:** Tests for `describe_app` and JSON Schema fidelity.

---

## 3. Ordered Implementation Workflow

### Step 1: Self-Contained Test Design
1. Do not require external async plugins (such as `pytest-asyncio`).
2. Write synchronous test functions using `asyncio.run(_run())` for async execution.
3. Keep test functions self-contained, readable, and focused on single contract assertions.

### Step 2: Positive & Negative Assertions
1. Test the happy path (valid types pass and produce `Success[T]`).
2. Test the failure path:
   - Verify `ValidationError.message`.
   - Verify `ValidationError.path` tuple.
   - Verify canonical projection in `invoke_result` (`FailureCode.INVALID_INPUT`).
3. Test negative evidence:
   - Verify that unsupported types (`dict[int, str]`, `set[T]`, recursive dataclasses) raise `SchemaError` at compile time.

### Step 3: Test Execution & Gate Verification
1. Run the test suite:
   ```powershell
   pytest -v
   ```
2. Verify code quality and formatting:
   ```powershell
   ruff check .
   ruff format --check .
   ```

---

## 4. Operational Boundaries & Negative Constraints

- **Do NOT introduce unnecessary test dependencies:** Rely on standard `pytest` and `asyncio.run()`.
- **Do NOT mock Agnara core:** Tests must execute real `StandardSchemaAdapter`, `ExecutionPlan`, and `invoke_result()` mechanics.
- **Do NOT write speculative tests:** Never test for features that exist only in later Agnara releases.

---

## 5. Validations & Definition of Done

The testing workflow is complete when:
- [ ] All 36 tests execute cleanly and pass in `pytest -v`.
- [ ] Tests verify both positive support and negative compile-time rejections.
- [ ] No warnings are emitted during test collection or execution.
