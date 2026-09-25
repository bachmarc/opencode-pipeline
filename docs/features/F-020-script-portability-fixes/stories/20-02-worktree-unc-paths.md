# Story 20-02 — Fix UNC path handling in worktree_setup.py

Status: Planned
Feature: script-portability-fixes (F-020)

## Context / Purpose

`worktree_setup.py` passes worktree paths as `cwd=str(worktree_path)` to `subprocess.run()`.
On Windows, when the project lives on a UNC network path (e.g., `\\192.168.1.1\share\project`),
Python's `subprocess.run(cwd="\\\\...")` fails with `WinError 267: The directory name is
invalid`. The Windows subprocess API does not accept UNC paths as `cwd`.

Git itself handles UNC paths correctly via `git -C <path> <command>`. The fix is to replace
`cwd=<path>` with `git -C <path>` for all subprocess calls that use a worktree path as `cwd`.
The main repo root (always a local path in the dev clone) is unaffected.

Affected call sites in `worktree_setup.py`:
- `cmd_remove()`: `git status --porcelain` with `cwd=str(worktree_path)`
- `cmd_list()`: `git symbolic-ref --short HEAD` with `cwd=path`
- `cmd_list()`: `git status --porcelain` with `cwd=path`

## Requirements

- All `subprocess.run()` calls that use a worktree path as `cwd` must be replaced with
  `git -C <path> <subcommand>` (no `cwd` argument for those calls).
- Calls that use `repo_root` as `cwd` (main repo operations) are NOT changed — they are
  always local paths.
- The script must work on both local paths and UNC paths (`\\server\share\...`).
- All existing tests for `worktree_setup.py` must continue to pass.
- No new external dependencies — stdlib only.

## Developer Targets (exactly, no more / no less)

- `scripts/worktree_setup.py`:
  - `cmd_remove()`: change `subprocess.run(["git", "status", "--porcelain"], cwd=str(worktree_path), ...)`
    to `subprocess.run(["git", "-C", str(worktree_path), "status", "--porcelain"], ...)` (remove `cwd`).
  - `cmd_list()`: change `subprocess.run(["git", "symbolic-ref", "--short", "HEAD"], cwd=path, ...)`
    to `subprocess.run(["git", "-C", path, "symbolic-ref", "--short", "HEAD"], ...)` (remove `cwd`).
  - `cmd_list()`: change `subprocess.run(["git", "status", "--porcelain"], cwd=path, ...)`
    to `subprocess.run(["git", "-C", path, "status", "--porcelain"], ...)` (remove `cwd`).
  - Update module docstring to note UNC-path compatibility via `git -C`.
  - Update docstrings and module headers in every file you change — code documentation is
    the source of truth.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `worktree_setup.py` contains no `cwd=str(worktree_path)` or `cwd=path` for worktree-local
  git commands (only `cwd=str(repo_root)` for repo-level commands remains).
- All worktree-local git commands use `git -C <path>` pattern.
- All existing tests pass (`pytest tests/ -x`).

## Test criteria (must exist BEFORE implementation)

- `tests/test_worktree_setup.py`: add test `test_worktree_git_commands_use_dash_c` — inspect
  the subprocess call arguments captured by a mock; assert that calls for worktree-local
  operations include `"-C"` and the worktree path in the args list, and do NOT pass `cwd=`
  pointing to the worktree path.
- The new test must be in the existing test file (not a new file).
