---
name: documentation
description: Standards and synchronization rules for maintaining Agnara typed capability contracts documentation.
---

# Documentation Skill

Use this skill when reading, authoring, or updating documentation in **Agnara Historical Reference Application #006 (`agnara-typed-contracts`)**.

---

## 1. When to Use This Skill

Activate this skill whenever:
- Updating or auditing `README.md`, `ARCHITECTURE.md`, `AGENTS.md`, or `docs/contracts_guide.md`.
- Documenting typed contract mechanics, schema compilation, or introspection snapshots.
- Adding or revising negative evidence for unsupported types in `0.1.0a3`.
- Maintaining the support matrix comparing Python typing vs Agnara runtime behavior.
- Recording historical release notes in `CHANGELOG.md`.

---

## 2. Relevant Inputs

- **`README.md`:** Human-oriented pedagogical guide and reference manual.
- **`AGENTS.md`:** Machine-oriented operational contract for AI coding agents.
- **`ARCHITECTURE.md`:** Architectural deep dive into the schema port, adapter mechanics, and validation boundaries.
- **`docs/contracts_guide.md`:** Practical developer guide for designing clear and stable capability contracts.
- **`CHANGELOG.md`:** Versioned release history under Keep a Changelog.

---

## 3. Ordered Implementation Workflow

### Step 1: Conceptual Separation Audit
Ensure all documentation strictly separates the 4 fundamental layers:
1. **Python annotation:** What the Python source code declares.
2. **Agnara introspection:** What Agnara observes and retains about the declaration (`describe_app`).
3. **Agnara validation:** What Agnara actually verifies during invocation (`_validate_inputs`).
4. **Machine-readable contract:** The protocol-neutral data schema exported in a3 (`InputDescriptor.schema`).

### Step 2: Historical Baseline Protection
1. Verify that `agnara==0.1.0a3` and CPython >= 3.14 are prominently cited.
2. Ensure the Historical / Frozen status is visibly displayed.
3. Confirm that no speculative or post-a3 APIs are described as existing in `0.1.0a3`.

### Step 3: Support Matrix Maintenance
Maintain an accurate support matrix reflecting actual verified behavior:
- Document what is supported (`int`, `str`, `float`, `bool`, `bytes`, `None`, `list[T]`, `dict[str, T]`, `tuple[...]`, `@dataclass`, `StrEnum`, `Literal[...]`).
- Document what is explicitly rejected (`dict[int, str]`, `set[T]`, recursive dataclasses, `InitVar`, PEP 695 `TypeAliasType`).
- Document what is not enforced at runtime (handler return values).

### Step 4: Cross-Document Consistency
1. `README.md` educates and demonstrates.
2. `AGENTS.md` governs agent operations and invariants.
3. `ARCHITECTURE.md` specifies internal mechanisms and design rationales.
4. Avoid duplicate explanations; cross-reference documents cleanly.

---

## 4. Operational Boundaries & Negative Constraints

- **No Speculative Claims:** Never describe features from later Agnara versions as present in `0.1.0a3`.
- **No Attributing Python Features to Agnara:** If Python permits something (e.g. passing a string to a dataclass constructor) but Agnara rejects it or doesn't validate it, document the exact boundary.
- **No Placeholder Text:** Never leave `TODO`, `TBD`, or temporary notes in public documentation.

---

## 5. Validations & Definition of Done

The documentation workflow is complete when:
- [ ] `README.md` and `AGENTS.md` are aligned with the historical baseline.
- [ ] The support matrix matches the passing test suite results.
- [ ] Markdown files pass formatting checks with `ruff format --check .`.
