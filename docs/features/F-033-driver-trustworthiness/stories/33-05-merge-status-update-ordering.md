# Story 33-05 — Merge Status Update Before Post-Merge Suite

Status: Planned
Feature: driver-trustworthiness (F-033)

## Codebase Snapshot

- `scripts/merge_if_passed.py` — `main()` function (around L415-443): after a successful
  merge, `run_post_merge_suite()` is called at L422, then `_update_story_status()` at L430.
  The post-merge suite runs all configured tests (~180s) before the status update runs.
- `tests/test_merge_if_passed.py` — 12 tests. `test_merge_writes_done_status` (added by
  33-01) tests the status update in isolation but does not verify ordering relative to the
  post-merge suite.

## Context / Purpose

Story 33-01 added `_update_story_status()` to write `Status: Done (merged as <sha>)` after
merge. However, it was placed AFTER `run_post_merge_suite()` in the call sequence. The
post-merge suite runs the full test suite (~180s). When the shell caller sets a timeout of
180s, the process is SIGTERMed before `_update_story_status()` ever runs — the status update
never happens. Result: story files stay at `Status: Planned`, driver.py emits false
`merge-candidate` actions for all merged stories (reproduced in session 2026-11-15).

Fix: move the status update to BEFORE `run_post_merge_suite()`. The status update is fast
(file write) and must happen atomically with the merge, not as a post-suite cleanup step.

## Requirements

1. In `merge_if_passed.py` `main()`, the `_update_story_status()` call (and surrounding
   story-ID extraction) is moved to BEFORE the `run_post_merge_suite()` call.
2. Order after fix:
   1. `merge_branch(branch)` → success
   2. Extract story ID, find story file, call `_update_story_status()` ← moved here
   3. `run_post_merge_suite()` ← unchanged, still runs
   4. Build output JSON, print, return exit code
3. No other logic changes. Module docstring updated to document the ordering.

## Developer Targets (exactly, no more / no less)

- `scripts/merge_if_passed.py`:
  - Move the status-update block (story ID extraction + `_find_story_file` + `_update_story_status`
    + WARNING print) from after `run_post_merge_suite()` to before it.
  - Update the inline comment to document the ordering rationale.
  - Update module docstring ordering note.
- `tests/test_merge_if_passed.py`:
  - `test_status_update_before_post_merge_suite` — verify that `_update_story_status` is called
    before `run_post_merge_suite` in the call sequence (mock both; assert status update mock
    called before suite mock via `call_args_list` ordering or `side_effect` sequencing).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain.
- `_update_story_status()` is invoked before `run_post_merge_suite()` in `main()`.
- `test_status_update_before_post_merge_suite` passes.
- All 12 existing `test_merge_if_passed.py` tests still pass.

## Test criteria (must exist BEFORE implementation)

QA may augment or correct these criteria during the QA phase.

- `test_status_update_before_post_merge_suite` — mock both `_update_story_status` and
  `run_post_merge_suite`; assert status update mock was called before suite mock.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy)
- [ ] Format check clean (black)
- [ ] Audit clean — n/a
