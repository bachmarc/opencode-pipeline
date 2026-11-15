# Story 35-01 — Ergonomics Fixes

Status: Done (merged as 601d65a)
Feature: pipeline-ergonomics (F-035)

## Codebase Snapshot

- `scripts/worktree_setup.py` — L2–15: module docstring containing `\share\...` on L13
  (part of the UNC-path example). Python 3.12+ raises `SyntaxWarning: invalid escape
  sequence '\s'` because `\s` in a non-raw docstring is an invalid escape; becomes
  `SyntaxError` under `python -W error`. Total 326 lines.
- `tests/test_worktree_setup.py` — 7 tests (L101–L240). `test_script_exists` at L101
  imports/runs the script; the SyntaxWarning surfaces here in strict mode.

## Context / Purpose

Two small quality-of-life fixes from VirtOffice session 2026-11-15 (TODO.md → T-003):

1. **SyntaxWarning in `worktree_setup.py`:** the UNC-path example in the module
   docstring contains `\share` — an invalid escape sequence that generates a noisy
   `SyntaxWarning` on every import. Trivial fix: `\\share` in the docstring.

2. **Documenter fallback in `AGENTS.md`:** when the `documenter` subagent hits a usage
   limit, the merge is blocked (missing `docs: reconcile` commit) and no fallback is
   documented. The architect is left to improvise. Fix: add a one-paragraph fallback
   rule to `AGENTS.md` stating that the architect may commit `docs: reconcile` directly
   in the worktree (scoped to story files and module docstrings only, no logic changes)
   when the documenter subagent is unavailable.
   Note: AGENTS.md is within the architect's direct-edit scope. The architect will
   update AGENTS.md as a planning commit; this story covers only the code fix.

## Requirements

1. `scripts/worktree_setup.py` docstring (L13): `\share` → `\\share` so no
   `SyntaxWarning` is emitted on import or compilation.
2. `python -W error -c "import scripts.worktree_setup"` (or equivalent `py_compile`)
   exits cleanly with no warning or error.
3. Module docstring of `worktree_setup.py` is otherwise unchanged (no content drift).

## Developer Targets (exactly, no more / no less)

- `scripts/worktree_setup.py`:
  - Line 13: change `\share` to `\\share` in the docstring.
  - No other changes.
- `tests/test_worktree_setup.py`:
  - `test_no_syntax_warnings` — `py_compile.compile('scripts/worktree_setup.py',
    doraise=True)` succeeds (exits without SyntaxWarning/SyntaxError).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `python -W error scripts/worktree_setup.py --help` (or `py_compile` equivalent)
  exits 0 without SyntaxWarning.
- `test_no_syntax_warnings` passes.
- All 7 existing `test_worktree_setup.py` tests still pass.
- No other content in `worktree_setup.py` changed.

## Test criteria (must exist BEFORE implementation)

- `tests/test_worktree_setup.py::test_no_syntax_warnings` — `py_compile.compile` on
  `scripts/worktree_setup.py` with `doraise=True` does not raise `py_compile.PyCompileError`.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy)
- [ ] Format check clean (black)
- [ ] Audit clean — n/a (no package registry)
