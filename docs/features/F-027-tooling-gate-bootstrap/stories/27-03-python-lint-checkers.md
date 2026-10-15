# Story 27-03 — Python Lint Checkers: mypy, ruff, black

Status: Planned
Feature: Tooling-Gate Bootstrap (F-027)

## Codebase Snapshot

- `scripts/qa_compress.py` — same inline pattern as 27-02. `pytest_check()` at line 63
  is the reference implementation for Python tool invocation. CHECKERS dict at lines ~563–578.
- No existing Python lint checker in qa_compress.py or qa_checkers/.
- `tests/` — fake-binary test pattern for reference (see jest or rspec checker tests).

## Context / Purpose

Python projects using the pipeline today declare `{"checkers": ["pytest"]}` — which covers
tests but not type-checking or code quality. A Python project can silently accumulate
type errors and style violations that never block QA. This story adds `mypy`, `ruff`,
and `black` as first-class checkers so Python projects get the same gate coverage
as JS/TS projects after 27-02.

`ruff` subsumes flake8/isort/pyflakes and is the modern Python linter. `black` is the
formatter. `mypy` is the type-checker. Together they cover the full Python quality stack.

## Requirements

1. `mypy_check()` — runs `mypy .` (or `mypy src/` if `src/` exists). Invocation:
   `mypy` on PATH. Not found: `"mypy not found\n"`, exit 1.
   Compressed output: error count + first 20 type errors on failure. On success: `"mypy: 0 errors\n"`.

2. `ruff_check()` — runs `ruff check .`. Invocation: `ruff` on PATH.
   Not found: `"ruff not found\n"`, exit 1.
   Compressed output: violation count + first 20 violation lines on failure.
   On success: `"ruff: 0 violations\n"`.

3. `black_check()` — runs `black --check .`. Invocation: `black` on PATH.
   Not found: `"black not found\n"`, exit 1.
   Compressed output: list of reformattable files (max 20) on failure.
   On success: `"black: all files formatted\n"`.

4. All three registered in `CHECKERS` dict as `"mypy"`, `"ruff"`, `"black"`.

## Developer Targets (exactly, no more / no less)

- `scripts/qa_compress.py`: Add three inline checker functions after `prettier_check()`:
  - `mypy_check() -> tuple[str, int]`
  - `ruff_check() -> tuple[str, int]`
  - `black_check() -> tuple[str, int]`
  Add to CHECKERS dict: `"mypy": mypy_check`, `"ruff": ruff_check`, `"black": black_check`.
  Update module docstring to include the new checker names.

- `tests/test_qa_checkers_python_lint.py` (new file): 9 tests minimum (3 per checker).
  Same fake-binary pattern as other checker tests.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `qa_compress.py` CHECKERS dict contains `"mypy"`, `"ruff"`, `"black"`.
- Each checker: clear "not found" exit 1 when binary missing.
- Each checker: compressed summary output (not raw log).
- All 9+ tests pass. No existing tests broken.

## Tooling Gates (mandatory — QA checks ALL of these)

- [ ] Tests green (`pytest`)
- [ ] Lint clean — N/A (framework's own qa_config.json has no ruff)
- [ ] Typecheck clean — N/A
- [ ] Format check clean — N/A
- [ ] Audit clean — N/A

## Test criteria (must exist BEFORE implementation)

- `test_mypy_check_success` — fake `mypy` exits 0 → exit 0, "0 errors".
- `test_mypy_check_failure` — fake `mypy` exits 1 with type errors → exit 1, compressed errors.
- `test_mypy_check_not_found` — no mypy → exit 1, "not found".
- `test_ruff_check_success` — fake `ruff check .` exits 0 → exit 0, "0 violations".
- `test_ruff_check_failure` — fake `ruff` exits 1 with violations → exit 1, violation lines.
- `test_ruff_check_not_found` — no ruff → exit 1, "not found".
- `test_black_check_success` — fake `black --check` exits 0 → exit 0, "all files formatted".
- `test_black_check_failure` — fake `black` exits 1 listing files → exit 1, file list.
- `test_black_check_not_found` — no black → exit 1, "not found".
