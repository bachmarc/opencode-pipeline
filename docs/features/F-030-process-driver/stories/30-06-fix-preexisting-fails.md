# Story 30-06 — Fix pre-existing test failures (merge-gate unblock)

Status: In Progress
Feature: Process Driver (F-030)

## Codebase Snapshot

- `tests/test_merge_if_passed.py` — 6 subprocess call sites (lines 49, 81, 113,
  216, 323, 430) invoke `["python", str(SCRIPT_PATH), ...]`. This machine has
  no `python` on PATH (only `python3`) → `FileNotFoundError` in all 6 tests.
  The repo convention is `#!/usr/bin/env python3` (see
  `scripts/merge_if_passed.py` line 1).
- `tests/test_migration.py::test_all_stories_have_feature_reference` (line
  116-123) asserts every story file has a `Feature:` line. Fails on
  `docs/features/F-029-worktree-hygiene/stories/29-01-worktree-cleanup-script.md`
  — that story was authored directly by the architect without the
  `Feature:` metadata line (see story template: `Feature: <feature-name>
  (<feature-id>)` after the Status line).
- Both failure classes exist on `main` at the wave-1 branch base and were
  verified independently by all four wave-1 developers via `git stash`
  (documented in their QA reports).

## Context / Purpose

Wave 1 of F-030 (stories 30-01, 30-03, 30-05, 31-01) is implemented and QA'd
with verdicts recorded, but `qa_compress.py` runs the full suite with AND
semantics — the 8 pre-existing failures fail every QA gate and would block
all wave-1 merges. User decision (2026-10-31): fix via a normal fix story
(gate discipline stays intact) instead of force-merging or off-loop
housekeeping.

## Requirements

1. `tests/test_merge_if_passed.py`: replace every bare `"python"` subprocess
   executable with `sys.executable` (add the import if missing). No other
   changes to the tests' semantics — fixtures, assertions and expectations
   stay identical.
2. `docs/features/F-029-worktree-hygiene/stories/29-01-worktree-cleanup-script.md`:
   add the missing `Feature: F-029 worktree-hygiene` line immediately after
   the title (before the first `##` heading). No other content changes.
3. STORIES.md: add table row `| 30-06-fix-preexisting-fails | Fix pre-existing
   test failures: test_merge_if_passed sys.executable + story 29-01 Feature:
   line | Planned | F-030 process-driver |`.

## Developer Targets (exactly, no more / no less)

- `tests/test_merge_if_passed.py` — the 6 call sites above.
- `docs/features/F-029-worktree-hygiene/stories/29-01-worktree-cleanup-script.md`
  — one added line.
- `STORIES.md` — one added table row; set this story's Status to In Progress.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `tests/test_merge_if_passed.py` contains no bare `"python"` executable
  string; uses `sys.executable` (grep-verified).
- All 6 `test_merge_if_passed.py` tests pass locally.
- `tests/test_migration.py` passes completely (8 tests).
- Story 29-01 doc contains the line `Feature: F-029 worktree-hygiene`.
- `scripts/merge_if_passed.py` itself is NOT modified (targets are test-side
  only).

## Test criteria (must exist BEFORE implementation)

- No new test files. The criteria are the existing failing tests
  (`test_merge_if_passed.py` 6 tests, `test_migration.py::test_all_stories_have_feature_reference`)
  flipping from FAIL to PASS. Verification before implementation: run
  `python3 -m pytest tests/test_merge_if_passed.py tests/test_migration.py -q`
  → 7 failures; after implementation → all green.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest)
- [ ] Lint clean (ruff) — if configured
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black) — if formatter configured
