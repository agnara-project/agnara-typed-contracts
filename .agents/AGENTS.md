# Agent Skills & Verification Registry

This directory contains specialized agent context for **Agnara Historical Reference Application #006 (`agnara-typed-contracts`)**.

## Pinned Baseline
- Framework: `agnara==0.1.0a3`
- Runtime: CPython >= 3.14
- Status: Historical / Frozen

## Critical Invariants
1. Do not update `agnara` past `0.1.0a3`.
2. Do not introduce Pydantic or external schema libraries into core.
3. Keep tests clean, self-contained, using `asyncio.run()` without external plugins.
4. Verify tests and linting before committing:
   - `pytest -v`
   - `ruff check .`
   - `python app.py`
