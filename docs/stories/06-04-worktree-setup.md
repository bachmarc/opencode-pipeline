# Story 06-04 — Worktree setup script

Status: Planned
Traceability: REQ-013.1 → Design §13

## Definition

Replace LLM free-hand worktree/branch creation with a deterministic Python script.
The Architect calls this script instead of running git commands directly.

## Development goal

After this story, `scripts/worktree_setup.py` creates worktrees atomically, validates
story IDs, and handles error cases. Agents call the script and parse its JSON output.

## Developer Targets (exactly, no more / no less)

- Create `scripts/worktree_setup.py`:
  - `worktree_setup.py create <story-id>`:
    - Validates story-id exists in `docs/features/*/stories/` (or `docs/stories/` for backward compat)
    - Derives slug deterministically from story filename
    - Creates `.worktrees/<id>-<slug>/` and `feature/<id>-<slug>` branch
    - Verifies `main` is clean before branching
    - Outputs JSON: `{"worktree": "<path>", "branch": "<name>", "story_file": "<path>"}`
    - Exit code 0 success, 1 story not found, 2 dirty main, 3 worktree already exists
  - `worktree_setup.py remove <story-id>`:
    - Removes worktree (after checking no uncommitted changes)
    - Outputs JSON: `{"removed": true, "path": "<path>"}`
  - `worktree_setup.py list`:
    - Lists all worktrees with branch and status
    - Outputs JSON array
- Script uses only stdlib (pathlib, subprocess, json, argparse)

## Acceptance criteria (checked by qa-manager)

- Script creates worktree + branch correctly for a valid story ID
- Script refuses to create worktree for non-existent story (exit 1)
- Script refuses to create worktree if main is dirty (exit 2)
- Script refuses to create duplicate worktree (exit 3)
- All output is valid JSON on stdout
- Remove checks for uncommitted changes before deleting

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_worktree_setup.py::test_script_exists` — script exists and compiles
- `tests/test_worktree_setup.py::test_create_valid_story` — creates worktree for existing story (uses tmp_path with git init)
- `tests/test_worktree_setup.py::test_create_nonexistent_story` — exit code 1 for missing story
- `tests/test_worktree_setup.py::test_create_duplicate` — exit code 3 when worktree exists
- `tests/test_worktree_setup.py::test_list_worktrees` — lists created worktrees as JSON
- `tests/test_worktree_setup.py::test_output_is_json` — stdout is valid JSON for all subcommands
