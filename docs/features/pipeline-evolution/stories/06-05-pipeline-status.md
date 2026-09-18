# Story 06-05 — Pipeline status aggregation script

Status: Planned
Traceability: REQ-013.2 → Design §13

## Definition

Replace LLM free-hand status aggregation (STORIES.md parsing, branch listing, pytest
correlation) with a deterministic script that outputs machine-readable JSON.

## Development goal

After this story, `scripts/pipeline_status.py` collects the full pipeline state and
outputs it as JSON. The QA-Manager and Architect consume this instead of manually
reading multiple files and running git commands.

## Developer Targets (exactly, no more / no less)

- Create `scripts/pipeline_status.py`:
  - `pipeline_status.py` (no args) — full status:
    - Reads `FEATURES.md` (or `docs/features/*/feature.md`) for feature/story state
    - Lists all `feature/*` branches (local + remote)
    - Maps branches to stories by naming convention
    - For each worktree in `.worktrees/`: dirty/clean, last commit
    - Reads `.pipeline/qa-state/*.json` for QA verdicts
    - Reads `.pipeline/intent.json` for open intents
    - Outputs combined JSON to stdout
  - `pipeline_status.py --feature <name>` — status for one feature
  - `pipeline_status.py --story <id>` — status for one story
  - Exit code 0 always (status is informational, not pass/fail)
- Script uses only stdlib

## Acceptance criteria (checked by qa-manager)

- Script outputs valid JSON for full status, per-feature, and per-story queries
- Feature status is correctly derived from story statuses
- Branches are correctly mapped to stories
- QA state and open intents are included when present
- Missing data (no worktrees, no QA state) does not crash — outputs empty fields

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_pipeline_status.py::test_script_exists` — script exists and compiles
- `tests/test_pipeline_status.py::test_output_is_valid_json` — output is parseable JSON
- `tests/test_pipeline_status.py::test_features_included` — output contains features list with status
- `tests/test_pipeline_status.py::test_empty_repo_no_crash` — script handles repo with no features/stories gracefully
- `tests/test_pipeline_status.py::test_story_filter` — `--story` flag filters to single story
