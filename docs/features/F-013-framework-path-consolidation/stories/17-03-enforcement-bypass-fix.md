# Story 17-03 — Enforcement Bypass Fix (merge_if_passed.py carries guard logic)

Status: Planned
Feature: F-013-framework-path-consolidation (F-013)

## Context / Purpose

`merge_if_passed.py` calls `git merge` via Python subprocess (`subprocess.run(["git", "merge",
…])`). The `merge-guard.ts` plugin only intercepts literal shell `git merge` commands — it
never sees the subprocess call. Result: the recommended, "safe" merge path bypasses its own
guard entirely.

The fix: `merge_if_passed.py` must carry the guard logic itself — check QA-PASS and
documenter-reconcile commit before calling `git merge`. The plugin guard remains as a second
layer for anyone who types `git merge` directly.

The documenter-reconcile check: the branch must have at least one commit whose message starts
with `docs: reconcile`. If not → abort with a clear error.

## Requirements

- `merge_if_passed.py` checks QA-PASS from `.pipeline/qa-state/<id>.json` using
  `verdicts[-1]["verdict"] == "PASS"` before calling `git merge`.
- `merge_if_passed.py` checks for a `docs: reconcile` commit on the branch via
  `git log <branch> --oneline --grep="^docs: reconcile"` before calling `git merge`.
- If QA-PASS missing → exit 1 with message "Merge blocked: no QA-PASS for <branch>".
- If documenter commit missing → exit 1 with message
  "Merge blocked: documenter not run on <branch>. Run /document first."
- If both checks pass → proceed with `git merge` as before.
- The plugin guards (`merge-guard.ts`, `documenter-guard.ts`) are NOT changed in this story.

## Developer Targets (exactly, no more / no less)

- `scripts/merge_if_passed.py` — add QA-PASS check and documenter-reconcile check before
  the `git merge` subprocess call. Update module docstring to document both checks.
- `tests/test_merge_if_passed.py` — extend existing tests (or create new file if none exists):
  test that missing QA-PASS → exit 1 + correct message; test that missing documenter commit →
  exit 1 + correct message; test that both present → `git merge` is called.

## Acceptance criteria (checked by qa-manager)

- `merge_if_passed.py` aborts with exit 1 and "Merge blocked: no QA-PASS" when PASS is missing.
- `merge_if_passed.py` aborts with exit 1 and "Merge blocked: documenter not run" when
  `docs: reconcile` commit is missing.
- `merge_if_passed.py` calls `git merge` when both checks pass.
- All tests pass.

## Test criteria (must exist BEFORE implementation)

- `tests/test_merge_if_passed.py::test_missing_qa_pass_exits_1` — no qa-state file → exit 1,
  message contains "no QA-PASS".
- `tests/test_merge_if_passed.py::test_fail_verdict_exits_1` — qa-state with FAIL → exit 1,
  message contains "no QA-PASS".
- `tests/test_merge_if_passed.py::test_missing_documenter_commit_exits_1` — PASS present but
  no `docs: reconcile` commit → exit 1, message contains "documenter not run".
- `tests/test_merge_if_passed.py::test_both_checks_pass_calls_git_merge` — PASS + documenter
  commit present → `git merge` subprocess is called (mock subprocess).
- Existing `merge_if_passed.py` tests remain green.
