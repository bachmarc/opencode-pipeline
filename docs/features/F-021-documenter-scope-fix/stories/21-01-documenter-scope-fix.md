# Story 21-01 — Documenter scope fix: branch-exclusive git log

Status: Planned
Feature: documenter-scope-fix (F-021)

## Context / Purpose

`merge_if_passed.py` and `documenter-guard.ts` both check for a `docs: reconcile` commit
before allowing a merge. Both use `git log <branch> --grep="docs: reconcile"` which traverses
the full ancestry — including `main`. Because Phase 12 left several `docs: reconcile` commits
on `main`, every feature branch inherits them in its history. The check therefore always passes,
even when the Documenter never ran on that branch.

The fix scopes the log to branch-exclusive commits only: `git log main..<branch>` (equivalently
`git log <branch> ^main`). This way only commits that exist on the feature branch but not yet
on `main` are considered.

## Requirements

1. `check_documenter_commit(branch)` in `merge_if_passed.py` uses `git log main..<branch>`
   (or `git log <branch> ^main`) instead of `git log <branch>`.
2. `documenterGuard` in `plugins/guards/documenter-guard.ts` uses the same branch-exclusive
   scope.
3. Existing tests for `check_documenter_commit` are updated/extended to verify that a
   `docs: reconcile` commit on `main` (ancestor) does NOT satisfy the check.
4. A test verifies that a `docs: reconcile` commit exclusively on the feature branch DOES
   satisfy the check.

## Developer Targets (exactly, no more / no less)

- `scripts/merge_if_passed.py`: change `check_documenter_commit()` — replace
  `["git", "log", branch, "--oneline", "--grep=^docs: reconcile"]`
  with `["git", "log", f"main..{branch}", "--oneline", "--grep=^docs: reconcile"]`.
  Update docstring to reflect new scope.
- `plugins/guards/documenter-guard.ts`: change the `gitLogCommand` string from
  `git log ${branch} --oneline --grep="docs: reconcile"`
  to `git log main..${branch} --oneline --grep="docs: reconcile"`.
  Update JSDoc comment.
- `tests/test_merge_if_passed.py`: add/update tests:
  - `test_documenter_commit_on_main_not_sufficient` — mock `git log main..<branch>` returning
    empty (commit only on main), assert `check_documenter_commit` returns False.
  - `test_documenter_commit_on_branch_sufficient` — mock returning a commit line, assert True.
- Update docstrings and module headers in every file you change — code documentation is the
  source of truth.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `check_documenter_commit()` in `merge_if_passed.py` uses `main..<branch>` scope (grep-verifiable).
- `documenterGuard` in `documenter-guard.ts` uses `main..${branch}` scope (grep-verifiable).
- `test_documenter_commit_on_main_not_sufficient` exists and passes.
- `test_documenter_commit_on_branch_sufficient` exists and passes.
- All existing tests still pass (`pytest` green).

## Test criteria (must exist BEFORE implementation)

- `tests/test_merge_if_passed.py::test_documenter_commit_on_main_not_sufficient`:
  mock `subprocess.run` for `git log main..<branch>` to return empty stdout →
  `check_documenter_commit(branch)` returns `False`.
- `tests/test_merge_if_passed.py::test_documenter_commit_on_branch_sufficient`:
  mock `subprocess.run` for `git log main..<branch>` to return one commit line →
  `check_documenter_commit(branch)` returns `True`.
