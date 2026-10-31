#!/usr/bin/env python3
"""Worktree cleanup script (Story 32-03; implements the 29-01 debt).

Classifies every git-registered worktree as merged / unmerged / dirty and
prints a JSON plan. With --apply it removes ONLY worktrees that are merged
AND clean, using the safe delete (`git worktree remove` + `git branch -d`,
which refuses unmerged branches). Unmerged and dirty worktrees are never
touched.

Modes:
  list (default; the literal `list` argument is also accepted)
      Classify and print a JSON plan. `.worktrees/` folders NOT registered
      with git are counted as orphan folders. Never mutates anything.
  --apply
      Remove only worktrees classified `merged` AND clean (no uncommitted
      or untracked changes). Only worktrees located under `.worktrees/` are
      candidates — the main working tree and any worktree registered outside
      `.worktrees/` are never removed. Output: JSON with removed entries
      (path + branch name) and any git errors.
  --purge-folders
      REQUIRES --apply (29-01 R1.5 contract). Deletes orphan `.worktrees/`
      folders WITHOUT a `.git` link file (inert remnants). Folders WITH a
      `.git` link (dead or alive, file or directory) are reported for manual
      review, never deleted.

Classification:
  dirty    — worktree has uncommitted/untracked changes (checked first:
             dirty wins, a dirty tree is never removed)
  merged   — clean and branch fully merged into the base branch
             (main preferred, then master; missing base -> unmerged)
  unmerged — clean but branch not merged (also: detached HEAD or deleted
             branch — conservative, survives --apply)

Exit codes:
  0 — plan or summary printed. The list/dry-run mode always exits 0
      (SUPERSEDES 29-01 R1.3, where a dry-run with work to do exited 1).
  1 — error: git failure in list mode; in --apply any git error (worktree
      remove, branch delete, purge scan) or filesystem error (purge
      deletion).
  2 — usage error (`--purge-folders` without `--apply`).

Supersession vs. 29-01 (audit 2026-10-31):
  - SUPERSEDES R1.3 exit codes: dry-run (list) exits 0 always.
  - SUPERSEDES R1.4 stash protection + prune step: only clean merged trees
    are removed, so nothing needs stashing; dirty/unmerged survive untouched.
  - KEEPS R1.5 purge contract: purge requires --apply; orphans without a
    `.git` link only.

Uses only stdlib (argparse, json, shutil, subprocess, sys, pathlib).
Git invocation follows worktree_setup.py conventions: `git -C <path>` for
worktree-local commands (UNC path compatibility), cwd=repo root otherwise.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

WORKTREES_DIR = ".worktrees"


def run_git(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a git command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 1, "", "git not found"


def get_base_branch(repo_root: Path) -> str | None:
    """Return the base branch name (main preferred, then master), or None."""
    for candidate in ("main", "master"):
        exit_code, _, _ = run_git(
            ["show-ref", "--verify", "--quiet", f"refs/heads/{candidate}"],
            cwd=repo_root,
        )
        if exit_code == 0:
            return candidate
    return None


def parse_registered_worktrees(
    repo_root: Path,
) -> tuple[list[dict[str, Any]], str | None]:
    """Parse `git worktree list --porcelain`.

    Returns: (entries, error). Each entry is {"path": <abs str>,
    "branch": <str | None>}; branch is None for detached/bare worktrees.
    error is None on success, a message string on git failure.
    """
    exit_code, stdout, stderr = run_git(
        ["worktree", "list", "--porcelain"], cwd=repo_root
    )
    if exit_code != 0:
        return [], stderr or "git worktree list failed"

    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            if current is not None:
                entries.append(current)
                current = None
            continue
        if line.startswith("worktree "):
            current = {"path": line[len("worktree "):].strip(), "branch": None}
        elif current is not None and line.startswith("branch "):
            ref = line[len("branch "):].strip()
            current["branch"] = ref.removeprefix("refs/heads/")
    if current is not None:
        entries.append(current)
    return entries, None


def is_worktree_clean(path: Path) -> bool:
    """True if the worktree has no uncommitted or untracked changes."""
    exit_code, stdout, _ = run_git(["-C", str(path), "status", "--porcelain"])
    return exit_code == 0 and stdout == ""


def is_branch_merged(branch: str, base: str, repo_root: Path) -> bool:
    """True if branch is fully merged into base (ancestor-or-equal)."""
    if branch == base:
        return False
    exit_code, _, _ = run_git(
        ["merge-base", "--is-ancestor", branch, base], cwd=repo_root
    )
    return exit_code == 0


def classify_worktree(
    entry: dict[str, Any], repo_root: Path, base: str | None
) -> str:
    """Classify one registered worktree: dirty / merged / unmerged.

    Dirty wins over merged (a dirty tree is never a removal candidate).
    A detached HEAD (no branch) counts as unmerged (conservative).
    """
    if not is_worktree_clean(Path(entry["path"])):
        return "dirty"
    branch = entry["branch"]
    if branch and base and is_branch_merged(branch, base, repo_root):
        return "merged"
    return "unmerged"


def is_cleanup_candidate(path: Path, repo_root: Path) -> bool:
    """True if the worktree lives under `.worktrees/` (removal candidate).

    The main working tree and any worktree registered outside `.worktrees/`
    are never removal candidates.
    """
    candidates_root = (repo_root / WORKTREES_DIR).resolve()
    try:
        path.resolve().relative_to(candidates_root)
    except ValueError:
        return False
    return True


def relative_path(repo_root: Path, path: Path) -> str:
    """Path relative to repo root for display; absolute as fallback."""
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def get_orphan_folders(
    repo_root: Path, registered_paths: set[str]
) -> list[Path]:
    """Return directories inside `.worktrees/` NOT registered with git."""
    worktrees_dir = repo_root / WORKTREES_DIR
    if not worktrees_dir.is_dir():
        return []
    orphans = []
    for child in sorted(worktrees_dir.iterdir()):
        if child.is_dir() and str(child.resolve()) not in registered_paths:
            orphans.append(child)
    return orphans


def scan(repo_root: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Scan the repo: classify registered worktrees and find orphans.

    Returns: (scan_result, error). scan_result has keys "worktrees"
    (list of dicts with abs_path / rel_path / branch / classification /
    eligible) and "orphans" (list of Paths). error is None on success.
    """
    base = get_base_branch(repo_root)
    entries, error = parse_registered_worktrees(repo_root)
    if error is not None:
        return None, error

    registered_paths = {str(Path(entry["path"]).resolve()) for entry in entries}
    worktrees = []
    for entry in entries:
        abs_path = Path(entry["path"])
        worktrees.append(
            {
                "abs_path": abs_path,
                "rel_path": relative_path(repo_root, abs_path),
                "branch": entry["branch"],
                "classification": classify_worktree(entry, repo_root, base),
                "eligible": is_cleanup_candidate(abs_path, repo_root),
            }
        )
    orphans = get_orphan_folders(repo_root, registered_paths)
    return {"worktrees": worktrees, "orphans": orphans}, None


def cmd_list(repo_root: Path) -> int:
    """Print the classification plan as JSON. Never mutates anything."""
    scan_result, error = scan(repo_root)
    if error is not None:
        print(json.dumps({"error": "git_error", "message": error}))
        return 1

    plan = {
        "mode": "list",
        "worktrees": [
            {
                "path": w["rel_path"],
                "branch": w["branch"],
                "classification": w["classification"],
                "action": (
                    "remove"
                    if w["eligible"] and w["classification"] == "merged"
                    else "keep"
                ),
            }
            for w in scan_result["worktrees"]
        ],
        "orphan_folders": len(scan_result["orphans"]),
    }
    print(json.dumps(plan, indent=2))
    return 0


def git_link_is_dead(git_link: Path) -> bool:
    """True if a `.git` link file points to a missing target (or is unreadable)."""
    try:
        content = git_link.read_text().strip()
    except OSError:
        return True
    if content.startswith("gitdir:"):
        target = content.split(":", 1)[1].strip()
    else:
        target = content
    if not target:
        return True
    return not Path(target).exists()


def purge_orphan_folders(
    repo_root: Path, orphans: list[Path]
) -> tuple[list[str], list[dict[str, Any]], list[dict[str, str]]]:
    """Delete orphan folders without `.git` link; report the others.

    Returns: (purged, reported, errors).
    - purged:  relative paths of deleted inert folders (no `.git` link)
    - reported: folders with a `.git` link (dead or alive) — never deleted
    - errors:  filesystem failures during deletion
    """
    purged: list[str] = []
    reported: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for folder in orphans:
        git_link = folder / ".git"
        if git_link.exists():
            reported.append(
                {
                    "path": relative_path(repo_root, folder),
                    "git_link_dead": git_link_is_dead(git_link),
                }
            )
            continue
        try:
            shutil.rmtree(folder)
        except OSError as exc:
            errors.append(
                {
                    "path": relative_path(repo_root, folder),
                    "step": "purge_folder",
                    "message": str(exc),
                }
            )
            continue
        purged.append(relative_path(repo_root, folder))
    return purged, reported, errors


def cmd_apply(repo_root: Path, purge_requested: bool) -> int:
    """Remove merged+clean worktrees (and optionally purge orphan folders).

    Returns: 0 on success, 1 if any git/filesystem error occurred.
    """
    scan_result, error = scan(repo_root)
    if error is not None:
        print(json.dumps({"error": "git_error", "message": error}))
        return 1

    removed: list[dict[str, str | None]] = []
    errors: list[dict[str, str]] = []
    for worktree in scan_result["worktrees"]:
        if not (worktree["eligible"] and worktree["classification"] == "merged"):
            continue
        exit_code, _, err = run_git(
            ["worktree", "remove", str(worktree["abs_path"])], cwd=repo_root
        )
        if exit_code != 0:
            errors.append(
                {
                    "path": worktree["rel_path"],
                    "step": "worktree_remove",
                    "message": err,
                }
            )
            continue
        branch = worktree["branch"]
        if branch:
            exit_code, _, err = run_git(
                ["branch", "-d", branch], cwd=repo_root
            )
            if exit_code != 0:
                errors.append(
                    {
                        "path": worktree["rel_path"],
                        "step": "branch_delete",
                        "message": err,
                    }
                )
                continue
        removed.append({"path": worktree["rel_path"], "branch": branch})

    output: dict[str, Any] = {
        "mode": "apply",
        "removed": removed,
        "errors": errors,
        "purged_folders": [],
        "reported_folders": [],
    }

    if purge_requested:
        # Re-scan AFTER removals: freshly removed trees are gone from the
        # registry (git deletes their directories), so they cannot appear
        # as orphan folders.
        entries, purge_scan_error = parse_registered_worktrees(repo_root)
        if purge_scan_error is not None:
            errors.append(
                {"step": "purge_scan", "message": purge_scan_error}
            )
        else:
            registered_paths = {
                str(Path(entry["path"]).resolve()) for entry in entries
            }
            orphans = get_orphan_folders(repo_root, registered_paths)
            purged, reported, purge_errors = purge_orphan_folders(
                repo_root, orphans
            )
            output["purged_folders"] = purged
            output["reported_folders"] = reported
            errors.extend(purge_errors)

    print(json.dumps(output, indent=2))
    return 1 if errors else 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Classify worktrees (merged/unmerged/dirty) and remove only "
            "merged+clean ones. Default: list mode, never mutates anything."
        ),
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["list"],
        default="list",
        help="'list' (default) prints the JSON classification plan",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="remove merged+clean worktrees under .worktrees/ and delete their branches",
    )
    parser.add_argument(
        "--purge-folders",
        dest="purge_folders",
        action="store_true",
        help=(
            "requires --apply: delete orphan .worktrees/ folders without a "
            ".git link; folders with a .git link are reported, never deleted"
        ),
    )

    args = parser.parse_args()
    repo_root = Path.cwd()

    if args.purge_folders and not args.apply:
        print(
            json.dumps(
                {
                    "error": "purge_requires_apply",
                    "message": "--purge-folders requires --apply",
                }
            )
        )
        print("Error: --purge-folders requires --apply.", file=sys.stderr)
        return 2

    if args.apply:
        return cmd_apply(repo_root, args.purge_folders)
    return cmd_list(repo_root)


if __name__ == "__main__":
    sys.exit(main())
