# Story 17-02 — Verdict Schema Fix (last_verdict → verdicts[])

Status: Planned
Feature: F-013-framework-path-consolidation (F-013)

## Context / Purpose

`merge-guard.ts` reads `status.last_verdict` to check for QA-PASS. This key is never written
by `qa_route.py`, which writes `{"verdicts": [{"verdict": "PASS"|"FAIL", …}]}`. The result:
anyone who types `git merge feature/…` directly in the shell gets blocked even when QA has
passed, because `status.last_verdict` is always `undefined`.

`merge_if_passed.py` reads `data["verdicts"][-1]["verdict"]` — correctly. The guard must be
aligned to the same schema.

## Requirements

- `merge-guard.ts` reads `status.verdicts[status.verdicts.length - 1].verdict` (last element
  of the `verdicts` array) instead of `status.last_verdict`.
- If `status.verdicts` is missing or empty → block with "Merge blocked: no QA-PASS".
- `qa_route.py` is NOT changed (it already writes the correct schema).
- `merge_if_passed.py` is NOT changed in this story (covered by 17-03).
- The schema is documented in `scripts/qa_route.py` module docstring:
  `# Schema: {"verdicts": [{"verdict": "PASS"|"FAIL", "branch": "…", "timestamp": "…", …}]}`

## Developer Targets (exactly, no more / no less)

- `plugins/guards/merge-guard.ts` — replace `status.last_verdict !== "PASS"` with
  `!status.verdicts?.length || status.verdicts[status.verdicts.length - 1].verdict !== "PASS"`.
  Update module docstring to document the schema it reads.
- `scripts/qa_route.py` — add schema documentation to module docstring (no logic change).
- `tests/test_merge_guard_verdict.py` — new test file: tests that a qa-state JSON with
  `{"verdicts": [{"verdict": "PASS"}]}` allows merge; tests that `{"verdicts": [{"verdict": "FAIL"}]}`
  blocks; tests that `{}` (no verdicts key) blocks; tests that `{"last_verdict": "PASS"}` (old
  schema) blocks.

## Acceptance criteria (checked by qa-manager)

- `merge-guard.ts` contains no `last_verdict` reference.
- `merge-guard.ts` reads `verdicts` array.
- `qa_route.py` module docstring documents the schema.
- All tests pass.

## Test criteria (must exist BEFORE implementation)

- `tests/test_merge_guard_verdict.py::test_pass_verdict_allows_merge` — `{"verdicts": [{"verdict": "PASS"}]}` → no error.
- `tests/test_merge_guard_verdict.py::test_fail_verdict_blocks_merge` — `{"verdicts": [{"verdict": "FAIL"}]}` → error contains "Merge blocked".
- `tests/test_merge_guard_verdict.py::test_missing_verdicts_blocks_merge` — `{}` → error contains "Merge blocked".
- `tests/test_merge_guard_verdict.py::test_old_schema_last_verdict_blocks_merge` — `{"last_verdict": "PASS"}` (no `verdicts` key) → error contains "Merge blocked".
- Existing merge-guard tests remain green.
