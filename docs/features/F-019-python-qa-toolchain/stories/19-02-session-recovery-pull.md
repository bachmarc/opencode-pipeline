# Story 19-02 — session_recovery.py: git pull at startup + test_resolve_by_id fix

Status: Planned
Feature: F-019-python-qa-toolchain (F-019)

## Context / Purpose

Two small but independent fixes in the framework tooling:

1. **`session_recovery.py` does not pull before scanning.** The AGENTS.md rule "pull before
   work" is documented but not enforced by the script. A developer who forgets the manual
   `git pull` gets a stale state scan — worktrees may show as behind, QA state may be
   outdated. The script already has `run_git_command()` — adding the pull is a three-line
   change. Pull failure (no remote, offline) must be non-fatal: print a warning to stderr
   and continue.

2. **`test_resolve_by_id` is fragile.** The test asserts `data["status"] == "Planned"` for
   story `06-01`, which has been `Done` for months. The test's actual purpose is to verify
   that `resolve_story.py` correctly resolves a story by ID and returns the right fields
   (id, slug, feature, branch, worktree). The status assertion is incidental and makes the
   test break whenever story statuses change. It should be removed from this test.

## Requirements

- `session_recovery.py` runs `git pull` on `repo_path` at the start of `main()`, before
  `collect_state()`.
- Pull output (stdout + stderr from git) is printed to stderr.
- If `git pull` fails (non-zero exit code), a warning is printed to stderr and execution
  continues normally — pull failure is non-fatal.
- `test_session_recovery.py` tests remain green: the `tmp_path` repos have no remote, so
  `git pull` will fail → the non-fatal path is exercised automatically.
- `test_resolve_by_id` in `tests/test_story_mgmt.py`: the `assert data["status"] == "Planned"`
  line is removed. All other assertions in the test remain unchanged.

## Developer Targets (exactly, no more / no less)

- `scripts/session_recovery.py` — in `main()`, before `collect_state(repo_path)`: call
  `run_git_command(["pull"], repo_path)`, print stdout+stderr to `sys.stderr`, print a
  warning if exit code is non-zero. Update the module docstring to mention the pull step.
- `tests/test_story_mgmt.py` — in `test_resolve_by_id()`: remove the line
  `assert data["status"] == "Planned"`. No other changes to this file.
- Update docstrings and module headers in every file you change — code documentation is the
  source of truth.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `session_recovery.py` contains a `git pull` call in `main()` before `collect_state()`.
- `session_recovery.py` handles pull failure non-fatally (warning + continue).
- `test_story_mgmt.py::test_resolve_by_id` no longer asserts `status == "Planned"`.
- All tests pass (0 failures).

## Test criteria (must exist BEFORE implementation)

- `tests/test_session_recovery.py` — existing tests remain green. The `tmp_path` repos have
  no remote → `git pull` fails → non-fatal path is exercised. No new test needed for the
  pull itself (the warning path is covered by the existing `test_empty_state` and similar
  tests running against repos without a remote).
- `tests/test_story_mgmt.py::test_resolve_by_id` — passes after removing the status
  assertion. All other assertions (id, slug, feature, branch, worktree, story_file) remain
  and still pass.
- New test: `tests/test_session_recovery.py::test_pull_called_on_startup` — run
  `session_recovery.py` in a `tmp_path` repo without a remote; assert exit code is 0
  (pull failure is non-fatal) and stderr contains either pull output or the warning string.
