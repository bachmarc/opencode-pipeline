# Story 33-02 — Booking Check

Status: Done (merged as 56ac4b2)
Feature: driver-trustworthiness (F-033)

## Codebase Snapshot

- `scripts/session_recovery.py` — `collect_state()` L264, `print_summary()` L306,
  `has_recovery_items()` L292; total 439 lines. Currently checks worktree staleness
  and open intents but does NOT cross-check claimed-done stories against git ancestry.
- `tests/test_merge_if_passed.py` — existing merge tests (9 tests) for adjacency awareness.
- `scripts/booking_check.py` and `tests/test_booking_check.py` — new files created by this story.

## Context / Purpose

VirtOffice had two stories (43-01/43-02) booked `✅ DONE (commit 8c40b28 / 341917e)` in
STORIES.md while neither commit was an ancestor of `main` — the actual fixes existed only
on the feature branches and were never merged. This was found only via manual
`git merge-base --is-ancestor` forensics; the driver never noticed because it trusts the
story-file status. Fix (D-6 from defect report): a deterministic consistency check that
for every story claiming `Done*` verifies the referenced SHA is an ancestor of main.
Surface violations in `session_recovery.py` so they appear at every session start.

## Requirements

1. New script `scripts/booking_check.py` scans all story files for `Status: Done*` lines
   that contain a SHA reference (pattern: `Done (.*<sha>.*)` where sha is 7+ hex chars).
2. For each found SHA, runs `git merge-base --is-ancestor <sha> HEAD` (or `main`).
3. Violations (SHA not an ancestor) are reported as `booking-vs-git divergence` items
   with the story file path and the commit SHA.
4. `scripts/session_recovery.py` calls `booking_check.py` logic (import or subprocess)
   and includes any violations in its summary output under a `Booking divergence` section.
5. CLI: `python scripts/booking_check.py` exits 0 when clean, 1 when divergence found.
   Output is human-readable lines, one per violation.
6. Module docstrings document the purpose and exit codes.

## Developer Targets (exactly, no more / no less)

- `scripts/booking_check.py` (new file):
  - `scan_done_statuses(repo_root: str) -> list[dict]` — returns list of
    `{"story_file": str, "sha": str, "status_line": str}` for all Done-with-SHA statuses.
  - `check_ancestry(sha: str, repo_root: str) -> bool` — runs
    `git merge-base --is-ancestor <sha> HEAD`, returns True when ancestor.
  - `run(repo_root: str) -> list[dict]` — returns violations list
    `{"story_file": str, "sha": str}`.
  - `main()` CLI entry point: exits 0 (clean) or 1 (violations), prints human-readable
    output.
  - Full module docstring.
- `scripts/session_recovery.py`:
  - Import/call `booking_check.run()` from `collect_state()` or `print_summary()`.
  - Add `booking_divergence` key to state dict with the violations list.
  - In `print_summary()`: print `Booking divergence (N):` section when violations exist.
  - Update module docstring.
- `tests/test_booking_check.py` (new file):
  - `test_no_violations_when_all_ancestors` — mock git to return 0; no violations.
  - `test_violation_when_sha_not_ancestor` — mock git to return 1; violation reported.
  - `test_no_sha_in_done_status_ignored` — `Status: Done` (no SHA) → not checked.
  - `test_cli_exit_0_clean` — CLI exits 0 when no violations.
  - `test_cli_exit_1_violation` — CLI exits 1 when violations.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `booking_check.py` exists and is importable.
- `scan_done_statuses` finds SHA-bearing `Done*` statuses; ignores bare `Done`.
- `check_ancestry` calls `git merge-base --is-ancestor` and returns correct bool.
- CLI exits 0/1 correctly.
- `session_recovery.py` prints `Booking divergence` section when violations present.
- All 5 new tests pass; existing session_recovery tests unaffected.

## Test criteria (must exist BEFORE implementation)

- `tests/test_booking_check.py::test_no_violations_when_all_ancestors` — all
  story-file SHAs are ancestors; `run()` returns empty list.
- `tests/test_booking_check.py::test_violation_when_sha_not_ancestor` — one SHA
  not an ancestor; `run()` returns one entry with the story file path and SHA.
- `tests/test_booking_check.py::test_no_sha_in_done_status_ignored` — `Status: Done`
  (no SHA) not flagged.
- `tests/test_booking_check.py::test_cli_exit_0_clean` — subprocess exit 0 when clean.
- `tests/test_booking_check.py::test_cli_exit_1_violation` — subprocess exit 1 when
  violation present.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy)
- [ ] Format check clean (black)
- [ ] Audit clean — n/a (no package registry)
