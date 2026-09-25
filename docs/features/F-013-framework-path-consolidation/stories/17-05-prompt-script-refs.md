# Story 17-05 — Prompts Drop Script Paths, Describe Actions Only

Status: Planned
Feature: F-013-framework-path-consolidation (F-013)

## Context / Purpose

Prompts (`agent/architect.md`, `agent/developer.md`, `agent/qa-manager.md`, skills) currently
reference framework scripts as `scripts/<name>.py` — a project-relative path that only exists
in the dogfood repo. In any other project these paths resolve to nothing.

The fix: prompts describe **what to do** (e.g. "run session recovery", "create a worktree",
"check story status") without specifying a path. The framework guards enforce the actual
execution. Where a script name is useful for recognition, it may be mentioned by name only
(e.g. "session_recovery.py") without a directory prefix.

This story covers all prompt files **except** `developer.md` and `qa-manager.md` test-runner
references (covered by 17-04) and the TypeScript guards (covered by 17-01).

## Requirements

- `agent/architect.md`: replace `scripts/<name>.py` references with action descriptions.
  E.g. `scripts/session_recovery.py` → "run session recovery"; `scripts/worktree_setup.py`
  → "set up the worktree"; `scripts/intent.py` → "track intent"; `scripts/merge_if_passed.py`
  → "merge if QA passed"; `scripts/create_story.py` → "create the story file".
- `agent/developer.md`: same for non-test-runner script references (test runner covered by 17-04).
- `agent/qa-manager.md`: same.
- `agent/documenter.md`: same.
- All skills under `skills/`: same.
- Script names (without path) may remain where they help recognition.
- No `scripts/` prefix anywhere in prompt files after this story.

## Developer Targets (exactly, no more / no less)

- `agent/architect.md` — replace all `scripts/<name>.py` occurrences with action descriptions.
  Update file header comment if it references script paths.
- `agent/developer.md` — same (non-test-runner references only).
- `agent/qa-manager.md` — same.
- `agent/documenter.md` — same.
- `skills/*.md` — same for all skill files.
- `tests/test_prompt_no_script_paths.py` — new test file: asserts that none of the above
  files contain the pattern `scripts/[a-z_]+\.py` (regex).

## Acceptance criteria (checked by qa-manager)

- No prompt file (`agent/*.md`, `skills/*.md`) contains `scripts/` followed by a `.py` filename.
- Script names without path prefix may remain (e.g. `session_recovery.py` alone is allowed).
- All tests pass.

## Test criteria (must exist BEFORE implementation)

- `tests/test_prompt_no_script_paths.py::test_architect_md_no_script_paths` — assert
  `agent/architect.md` contains no `scripts/[a-z_]+\.py` pattern.
- `tests/test_prompt_no_script_paths.py::test_developer_md_no_script_paths` — same for
  `agent/developer.md`.
- `tests/test_prompt_no_script_paths.py::test_qa_manager_md_no_script_paths` — same for
  `agent/qa-manager.md`.
- `tests/test_prompt_no_script_paths.py::test_documenter_md_no_script_paths` — same for
  `agent/documenter.md`.
- `tests/test_prompt_no_script_paths.py::test_skills_no_script_paths` — assert all files
  matching `skills/*.md` contain no `scripts/[a-z_]+\.py` pattern.
