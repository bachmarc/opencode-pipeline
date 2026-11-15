# Story 33-01 — Merge Status Update

Status: Done (merged as 701a96f)
Feature: driver-trustworthiness (F-033)

## Codebase Snapshot

- `scripts/merge_if_passed.py` — `extract_story_id()` L104, `check_qa_pass()` L118,
  `merge_branch()` L180, post-merge suite check around L260; total 376 lines.
  Currently merges the branch and updates STORIES.md prose (via session convention),
  but NEVER writes the story file's `Status:` line.
- `tests/test_merge_if_passed.py` — 9 tests covering QA-PASS check, documenter commit,
  post-merge suite check. Tests at L48, L73, L105, L137, L240, L347, L507, L535, L576.
- `docs/features/*/stories/*.md` — story files; the `Status:` line is the driver's
  status source (read by `scripts/driver.py` → `_read_status_line()` L557).

## Context / Purpose

`driver.py` reads story-file `Status:` lines as its authoritative source (not STORIES.md).
`merge_if_passed.py` never updates those lines after a merge — so all merged stories keep
their pre-dev status forever. On a mature project this generates dozens of false
`merge-candidate` and `spawn-qa` actions that drown the two or three genuine ones.
Fix (D-1 from the defect report): atomically write `Status: Done (merged as <sha>)` to
the story file as part of the merge step. Also print the `worktree_cleanup.py` invocation
hint so the developer knows to clean up (D-8).

## Requirements

1. After a successful merge, `merge_if_passed.py` updates the story file's `Status:` line
   to `Status: Done (merged as <short-sha>)` where `<short-sha>` is the 7-char merge commit
   SHA (or shorter standard git abbreviation). The update is atomic within the same
   function that performs the merge.
2. If the story file cannot be found or the `Status:` line is missing, the merge still
   succeeds but a warning is printed (`WARNING: could not update status in <path>`).
3. After a successful merge, `merge_if_passed.py` prints a cleanup hint:
   `Hint: run 'python scripts/worktree_cleanup.py --apply' to remove the merged worktree.`
4. The module docstring of `merge_if_passed.py` is updated to document the new
   story-file status update behaviour.

## Developer Targets (exactly, no more / no less)

- `scripts/merge_if_passed.py`:
  - Add helper `_update_story_status(story_file: Path, sha: str) -> bool` that rewrites
    the `Status:` line (or warns if not found). Called after successful merge.
  - In `merge_branch()` (or the calling logic): after merge commit, resolve the story file
    via `resolve_story.py`-compatible path lookup (or direct glob
    `docs/features/*/stories/<story-id>-*.md`), call `_update_story_status`, then print
    the cleanup hint.
  - Update module docstring to document new behaviour.
- `tests/test_merge_if_passed.py`:
  - `test_merge_writes_done_status` — after a successful merge, the story file's
    `Status:` line reads `Done (merged as <sha>)`.
  - `test_merge_status_update_missing_story_file_warns` — when the story file glob
    finds nothing, merge still succeeds and a warning is printed to stdout/stderr.
  - `test_merge_prints_cleanup_hint` — after successful merge, the cleanup hint line
    appears in the output.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `merge_if_passed.py` writes `Status: Done (merged as <sha>)` into the story file on
  successful merge (verified by `test_merge_writes_done_status`).
- If the story file is not found, merge still exits 0 and a warning is printed.
- Cleanup hint is printed after successful merge.
- All existing `test_merge_if_passed.py` tests still pass.
- Module docstring updated.

## Test criteria (must exist BEFORE implementation)

- `tests/test_merge_if_passed.py::test_merge_writes_done_status` — creates a tmp story
  file with `Status: Planned`, simulates a successful merge, asserts the file now contains
  `Status: Done (merged as`.
- `tests/test_merge_if_passed.py::test_merge_status_update_missing_story_file_warns` —
  no story file present in tmp fixture; merge exits 0, output contains "WARNING".
- `tests/test_merge_if_passed.py::test_merge_prints_cleanup_hint` — successful merge
  fixture; output contains `worktree_cleanup.py --apply`.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy)
- [ ] Format check clean (black)
- [ ] Audit clean — n/a (no package registry)
