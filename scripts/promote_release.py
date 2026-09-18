#!/usr/bin/env python3
"""Promote main branch to release branch.

Validates that main is clean and up-to-date, then fast-forward merges
release to current main HEAD and pushes to remote.

Exit codes:
  0 - success
  1 - dirty state or behind remote
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any


def run_git(cmd: list[str]) -> tuple[int, str, str]:
    """Run a git command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        ["git"] + cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_current_branch() -> str:
    """Get the current branch name."""
    code, stdout, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if code != 0:
        raise RuntimeError("Failed to get current branch")
    return stdout


def get_commit_hash(ref: str) -> str:
    """Get the commit hash for a given ref."""
    code, stdout, _ = run_git(["rev-parse", ref])
    if code != 0:
        raise RuntimeError(f"Failed to get commit hash for {ref}")
    return stdout


def is_main_clean() -> bool:
    """Check if main branch is clean (no uncommitted changes)."""
    code, stdout, _ = run_git(["status", "--porcelain"])
    if code != 0:
        return False
    return len(stdout) == 0


def is_main_up_to_date() -> bool:
    """Check if main is up-to-date with remote (not behind)."""
    # Fetch to ensure we have latest remote info
    code, _, _ = run_git(["fetch", "origin", "main"])
    if code != 0:
        return False
    
    # Check if main is behind origin/main
    code, stdout, _ = run_git(["rev-list", "--count", "main..origin/main"])
    if code != 0:
        return False
    
    behind_count = int(stdout) if stdout else 0
    return behind_count == 0


def promote_release() -> dict[str, Any]:
    """Promote main to release branch.
    
    Returns:
        dict with keys: promoted (bool), from (str), to (str), error (str, optional)
    """
    # Verify we're on main
    current_branch = get_current_branch()
    if current_branch != "main":
        return {
            "promoted": False,
            "error": f"Not on main branch (currently on {current_branch})",
        }
    
    # Check if main is clean
    if not is_main_clean():
        return {
            "promoted": False,
            "error": "main branch has uncommitted changes",
        }
    
    # Check if main is up-to-date with remote
    if not is_main_up_to_date():
        return {
            "promoted": False,
            "error": "main branch is behind origin/main",
        }
    
    # Get current main commit
    main_commit = get_commit_hash("main")
    
    # Check if release branch exists
    code, _, _ = run_git(["rev-parse", "--verify", "release"])
    release_exists = code == 0
    
    if not release_exists:
        # Create release branch from main
        code, _, stderr = run_git(["branch", "release", "main"])
        if code != 0:
            return {
                "promoted": False,
                "error": f"Failed to create release branch: {stderr}",
            }
    else:
        # Fast-forward merge release to main
        code, _, stderr = run_git(["checkout", "release"])
        if code != 0:
            return {
                "promoted": False,
                "error": f"Failed to checkout release: {stderr}",
            }
        
        code, _, stderr = run_git(["merge", "--ff-only", "main"])
        if code != 0:
            # Try to go back to main
            run_git(["checkout", "main"])
            return {
                "promoted": False,
                "error": f"Failed to fast-forward merge: {stderr}",
            }
        
        # Go back to main
        code, _, stderr = run_git(["checkout", "main"])
        if code != 0:
            return {
                "promoted": False,
                "error": f"Failed to checkout main: {stderr}",
            }
    
    # Push release to remote
    code, _, stderr = run_git(["push", "origin", "release"])
    if code != 0:
        return {
            "promoted": False,
            "error": f"Failed to push release: {stderr}",
        }
    
    # Get release commit after push
    release_commit = get_commit_hash("release")
    
    return {
        "promoted": True,
        "from": main_commit,
        "to": release_commit,
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Promote main branch to release branch"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON (default: human-readable)",
    )
    parser.parse_args()
    
    try:
        result = promote_release()
    except RuntimeError as e:
        result = {
            "promoted": False,
            "error": str(e),
        }
    
    # Always output JSON per story requirements
    print(json.dumps(result))
    
    return 0 if result.get("promoted") else 1


if __name__ == "__main__":
    sys.exit(main())
