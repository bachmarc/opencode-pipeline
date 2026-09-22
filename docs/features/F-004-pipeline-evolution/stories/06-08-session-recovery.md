# Story 06-08 — Session recovery script

Status: Done
Feature: pipeline-evolution (F-004)

## Context / Purpose

Create the central recovery script that runs at session start and collects the full
pipeline state: open intents, worktree conditions, QA state, feature claims. This is
what prevents the "session crashed, unclear where we are" problem.

## Requirements

After this story, `scripts/session_recovery.py` produces a comprehensive JSON report
that an agent can present to the user immediately at session start.

## Developer Targets (exactly, no more / no less)

- Create `scripts/session_recovery.py`:
  - `session_recovery.py` (no args) — collects:
    - Open intents from `.pipeline/intent.json` (depends on 06-02)
    - Worktrees from `.worktrees/`: path, branch, uncommitted files, staged files,
      merge conflicts, detached HEAD, last 3 commits, pushed-to-remote status
    - Main state: ahead/behind remote, dirty working tree
    - QA state from `.pipeline/qa-state/*.json`: last verdict, fail count per story
    - Feature claims from `docs/features/*/feature.md`: who has claimed what
  - Outputs JSON to stdout (full schema as in Design §11)
  - `session_recovery.py --check` — exit code 0 if nothing to recover, 1 if
    recovery items exist (for use in agent prompt conditional)
  - Human-readable summary to stderr
- Script uses only stdlib + calls `git` subprocess

## Acceptance criteria (checked by qa-manager)

- Script collects all five state dimensions (intents, worktrees, main, QA, claims)
- Missing state (no worktrees, no intents) produces empty fields, not errors
- `--check` exit code correctly reflects recovery state
- JSON output matches the schema from Design §11
- Stderr summary is human-readable

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_session_recovery.py::test_script_exists` — script exists and compiles
- `tests/test_session_recovery.py::test_empty_state` — clean repo produces valid JSON with empty fields
- `tests/test_session_recovery.py::test_open_intent_detected` — open intent in `.pipeline/intent.json` appears in output
- `tests/test_session_recovery.py::test_worktree_detected` — existing worktree appears with correct branch/status
- `tests/test_session_recovery.py::test_check_flag_clean` — `--check` returns 0 for clean state
- `tests/test_session_recovery.py::test_check_flag_dirty` — `--check` returns 1 when open intents exist
- `tests/test_session_recovery.py::test_output_is_valid_json` — stdout is parseable JSON
