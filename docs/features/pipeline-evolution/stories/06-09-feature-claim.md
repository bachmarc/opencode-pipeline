# Story 06-09 — Feature claim script

Status: Done
Feature: pipeline-evolution (F-004)

## Context / Purpose

Deterministic feature claiming for multi-user isolation. The script handles atomic
claim/release with git pull-check-commit-push, preventing race conditions that an LLM
cannot handle reliably.

## Requirements

After this story, `scripts/feature_claim.py` manages feature claims atomically.
No agent ever edits feature status directly — they call this script.

## Developer Targets (exactly, no more / no less)

- Create `scripts/feature_claim.py`:
  - `feature_claim.py claim <feature-name>`:
    - `git pull --rebase` first
    - Reads `docs/features/<name>/feature.md`
    - If status is `planned` or `released`: sets `status: claimed`, `owner: <user@host>`,
      `claimed_at: <ISO timestamp>`
    - Commits change, pushes to remote
    - If push fails (concurrent edit): retry (pull + re-check, max 3 attempts)
    - If already claimed by someone else: exit code 1 + error JSON
    - Creates `feature/<name>` branch if not exists
    - Outputs JSON: `{"claimed": true, "feature": "<name>", "owner": "<user@host>"}`
  - `feature_claim.py release <feature-name>`:
    - Resets status to `planned` (or `done` if all stories done), clears owner
    - Commits + pushes
    - Outputs JSON: `{"released": true, "feature": "<name>"}`
  - `feature_claim.py status`:
    - Lists all features with claim state
    - Outputs JSON array
  - `feature_claim.py check-stale [--hours 24]`:
    - Finds claims older than threshold
    - Outputs JSON array of stale claims
  - Exit codes: 0 success, 1 already claimed, 2 feature not found, 3 push conflict (max retries)
- Script uses only stdlib + git subprocess
- `user@host` is derived from `git config user.email` + `hostname`

## Acceptance criteria (checked by qa-manager)

- Claim succeeds for unclaimed feature
- Claim fails (exit 1) for already-claimed feature
- Release resets status correctly
- Status lists all features with current claim state
- Check-stale correctly identifies old claims
- Push-conflict retry logic works (at least the code path exists)

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_feature_claim.py::test_script_exists` — script exists and compiles
- `tests/test_feature_claim.py::test_claim_unclaimed` — claim succeeds, feature.md updated
- `tests/test_feature_claim.py::test_claim_already_claimed` — exit code 1 when already claimed
- `tests/test_feature_claim.py::test_release` — release resets status and owner
- `tests/test_feature_claim.py::test_status_output` — status outputs valid JSON array
- `tests/test_feature_claim.py::test_check_stale` — stale detection finds old claims
- `tests/test_feature_claim.py::test_claim_nonexistent` — exit code 2 for unknown feature
