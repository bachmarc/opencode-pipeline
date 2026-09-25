# Story 20-01 — Fix repo_root in resolve_story.py + story_status.py

Status: Planned
Feature: script-portability-fixes (F-020)

## Context / Purpose

`resolve_story.py` and `story_status.py` compute `repo_root` as:

```python
repo_root = Path(__file__).resolve().parent.parent
```

When the scripts are installed in `~/.config/opencode/scripts/` and called from a project
directory, this resolves to `~/.config/opencode/` (the framework repo), not the project
directory. The scripts therefore search for stories in the wrong location and silently
return "not found" for any project that is not the framework itself.

All other scripts (`merge_if_passed.py`, `pipeline_status.py`) correctly use a
`get_repo_root()` function that traverses upward from `Path.cwd()` looking for a `.git`
directory. These two scripts are the only outliers.

## Requirements

- `resolve_story.py` and `story_status.py` must determine `repo_root` by traversing upward
  from `Path.cwd()` until a `.git` directory is found (same logic as `merge_if_passed.py`).
- If no `.git` directory is found, fall back to `Path.cwd()` (same fallback as existing scripts).
- The `get_repo_root()` helper must be defined locally in each script (no shared import —
  scripts are standalone stdlib-only tools).
- Calling `resolve_story.py 04-01` from a project directory must find that project's story,
  not the framework's story.
- All existing tests for both scripts must continue to pass.

## Developer Targets (exactly, no more / no less)

- `scripts/resolve_story.py`:
  - Add `get_repo_root() -> Path` function (identical logic to `merge_if_passed.py`):
    traverse `Path.cwd()` upward, return first directory containing `.git`, fallback `Path.cwd()`.
  - In `main()`: replace `repo_root = Path(__file__).resolve().parent.parent` with
    `repo_root = get_repo_root()`.
  - Update module docstring to note the CWD-based repo root resolution.
- `scripts/story_status.py`:
  - Add `get_repo_root() -> Path` function (same logic).
  - In `main()`: replace `repo_root = Path(__file__).resolve().parent.parent` with
    `repo_root = get_repo_root()`.
  - Update module docstring to note the CWD-based repo root resolution.
- Update docstrings and module headers in every file you change — code documentation is
  the source of truth.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `resolve_story.py` contains a `get_repo_root()` function that uses `Path.cwd()` traversal.
- `story_status.py` contains a `get_repo_root()` function that uses `Path.cwd()` traversal.
- Neither script contains `Path(__file__)` for repo root determination.
- All existing tests pass (`pytest tests/ -x`).

## Test criteria (must exist BEFORE implementation)

- `tests/test_resolve_story.py`: add test `test_repo_root_uses_cwd` — monkeypatch `Path.cwd`
  to return a temp directory with a `.git` marker and a `docs/features/` structure; assert
  `get_repo_root()` returns the temp dir (not the script's parent).
- `tests/test_story_status.py`: add test `test_repo_root_uses_cwd` — same pattern: monkeypatch
  `Path.cwd`, assert `get_repo_root()` returns the mocked project root.
- Both new tests must be in the existing test files (not new files).
