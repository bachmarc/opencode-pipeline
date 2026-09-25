---
id: F-020
title: Script Portability Fixes
status: planned
owner: ""
req: []
---

## Vision

All framework scripts (`resolve_story.py`, `story_status.py`, `worktree_setup.py`) work
correctly regardless of where they are called from and on which OS/filesystem topology
(local drive, UNC network path, mapped drive).

## Context

Two portability bugs were reported by a user running the framework on a Windows UNC network path:

1. **Wrong `repo_root` in `resolve_story.py` + `story_status.py`:** Both scripts compute
   `repo_root = Path(__file__).resolve().parent.parent`, which resolves to the framework
   installation directory (`~/.config/opencode/`), not the project directory from which the
   script is called. All other scripts (`merge_if_passed.py`, `pipeline_status.py`) correctly
   use `get_repo_root()` with Git-traversal from `Path.cwd()`. These two scripts are the
   only outliers.

2. **UNC path failure in `worktree_setup.py`:** The script passes worktree paths as `cwd=`
   to `subprocess.run()`. On Windows, `subprocess.run(cwd="\\\\server\\share\\...")` fails
   with `WinError 267: The directory name is invalid` because the Python subprocess API on
   Windows does not accept UNC paths as `cwd`. Git itself handles UNC paths fine via
   `git -C <path>`.

## Stories

- 20-01-resolve-story-root (Planned)
- 20-02-worktree-unc-paths (Planned)
