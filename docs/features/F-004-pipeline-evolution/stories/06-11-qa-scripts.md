# Story 06-11 — QA routing and commit metadata scripts

Status: Done
Feature: pipeline-evolution (F-004)

## Context / Purpose

Deterministic scripts for QA verdict routing (FAIL → developer, BLOCKED → architect),
commit metadata generation, and merge validation. These replace LLM free-hand operations
in the QA cycle.

## Requirements

After this story, QA verdict routing with budget tracking, commit metadata, and merge
validation are script-based with proper state persistence.

## Developer Targets (exactly, no more / no less)

- Create `scripts/qa_route.py`:
  - `qa_route.py record <story-id> <verdict>` — records verdict in `.pipeline/qa-state/<story-id>.json`
  - `qa_route.py next <story-id>` — based on verdict history:
    - PASS → `{"action": "documenter", "branch": "..."}`
    - FAIL (count < 3) → `{"action": "developer-fix", "branch": "...", "fail_count": N}`
    - FAIL (count >= 3) → `{"action": "blocked-requirements", "fail_count": N}`
    - BLOCKED_Design (count < 2) → `{"action": "architect-fix", "design_fix_count": N}`
    - BLOCKED_Design (count >= 2) → `{"action": "blocked-requirements"}`
  - `qa_route.py history <story-id>` — full verdict history as JSON
  - Exit codes: 0 success, 1 story not found

- Create `scripts/prepare_commit_metadata.py`:
  - `prepare_commit_metadata.py` — reads `git diff --cached`:
    - Extracts changed file names
    - Identifies changed export symbols (Python: functions/classes via AST, other: file-level)
    - Finds dependent files (grep for imports of changed modules)
    - Runs `pytest --tb=no -q` for test result
    - Outputs formatted metadata string:
      `symbols: ... | breaks: none|breaking | affects: ... | tests: ...`
  - Exit code 0 always (informational)

- Create `scripts/merge_if_passed.py`:
  - `merge_if_passed.py <branch>`:
    - Checks `.pipeline/qa-state/<story-id>.json` for PASS verdict
    - If PASS: `git merge --no-ff <branch>` into current branch
    - If no PASS: exit code 1 + error JSON
    - Outputs JSON: `{"merged": true, "branch": "...", "commit": "..."}`
  - Exit code 0 merged, 1 no QA-PASS found, 2 merge conflict

- All scripts use only stdlib

## Acceptance criteria (checked by qa-manager)

- QA route correctly tracks verdict history in `.pipeline/qa-state/`
- Budget limits (3 FAIL, 2 design-fix) are enforced
- Commit metadata script produces correctly formatted output
- Merge validation refuses to merge without QA-PASS record
- All outputs are valid JSON

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_qa_scripts.py::test_qa_route_record` — records verdict to qa-state file
- `tests/test_qa_scripts.py::test_qa_route_next_pass` — PASS → documenter action
- `tests/test_qa_scripts.py::test_qa_route_next_fail_budget` — 3 FAILs → blocked-requirements
- `tests/test_qa_scripts.py::test_qa_route_history` — returns full history
- `tests/test_qa_scripts.py::test_commit_metadata_format` — output matches `symbols: ... | breaks: ...` format
- `tests/test_qa_scripts.py::test_merge_if_passed_no_pass` — exit code 1 without QA-PASS
- `tests/test_qa_scripts.py::test_merge_if_passed_with_pass` — exit code 0 with QA-PASS record
