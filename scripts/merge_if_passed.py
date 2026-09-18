#!/usr/bin/env python3
"""Merge validation script.

Checks .pipeline/qa-state/ for QA-PASS verdict before merging.

Usage:
  merge_if_passed.py <branch>

Behavior:
- Extracts story-id from branch name (e.g., feature/06-11-qa-scripts → 06-11)
- Checks .pipeline/qa-state/<story-id>.json for PASS verdict
- If PASS: git merge --no-ff <branch> into current branch
- If no PASS: exit code 1 + error JSON
- On merge conflict: exit code 2

Output: JSON to stdout
  Success: {"merged": true, "branch": "...", "commit": "..."}
  No PASS: {"error": "No QA-PASS found for story ..."}
  Conflict: {"error": "Merge conflict on branch ..."}

Exit codes:
  0 - Merged successfully
  1 - No QA-PASS record found
  2 - Merge conflict
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Find repo root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def extract_story_id(branch: str) -> str | None:
    """Extract story ID from branch name.
    
    Examples:
    - feature/06-11-qa-scripts → 06-11
    - feature/06-05-test → 06-05
    """
    # Match pattern: feature/<digits>-<digits>-...
    match = re.match(r"feature/(\d+-\d+)", branch)
    if match:
        return match.group(1)
    return None


def check_qa_pass(story_id: str) -> bool:
    """Check if story has QA-PASS verdict."""
    repo_root = get_repo_root()
    state_file = repo_root / ".pipeline" / "qa-state" / f"{story_id}.json"
    
    if not state_file.exists():
        return False
    
    try:
        data = json.loads(state_file.read_text())
        verdicts = data.get("verdicts", [])
        
        # Check if last verdict is PASS
        return bool(verdicts and verdicts[-1].get("verdict") == "PASS")
    except Exception:  # noqa: BLE001
        return False


def get_current_branch() -> str | None:
    """Get current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def get_commit_hash(branch: str) -> str | None:
    """Get commit hash for a branch."""
    result = subprocess.run(
        ["git", "rev-parse", branch],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def merge_branch(branch: str) -> tuple[bool, str | None]:
    """Merge branch with --no-ff flag.
    
    Returns: (success, commit_hash or error_message)
    """
    result = subprocess.run(
        ["git", "merge", "--no-ff", branch, "-m", f"Merge {branch}"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode == 0:
        # Get the merge commit hash
        commit_hash = get_commit_hash("HEAD")
        return True, commit_hash
    
    # Check if it's a merge conflict
    if "conflict" in result.stderr.lower() or "conflict" in result.stdout.lower():
        return False, "Merge conflict"
    
    return False, result.stderr or result.stdout


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Merge validation script"
    )
    parser.add_argument("branch", help="Branch to merge (e.g., feature/06-11-qa-scripts)")
    
    args = parser.parse_args()
    branch = args.branch
    
    # Extract story ID from branch name
    story_id = extract_story_id(branch)
    if not story_id:
        output = {
            "error": f"Could not extract story ID from branch name: {branch}",
        }
        print(json.dumps(output))
        return 1
    
    # Check for QA-PASS verdict
    if not check_qa_pass(story_id):
        output = {
            "error": f"No QA-PASS found for story {story_id}",
        }
        print(json.dumps(output))
        return 1
    
    # Attempt merge
    success, result = merge_branch(branch)
    
    if success:
        output = {
            "merged": True,
            "branch": branch,
            "commit": result,
        }
        print(json.dumps(output))
        return 0
    
    # Merge failed
    if "conflict" in result.lower():
        output = {
            "error": f"Merge conflict on branch {branch}",
        }
        print(json.dumps(output))
        return 2
    
    output = {
        "error": f"Merge failed: {result}",
    }
    print(json.dumps(output))
    return 1


if __name__ == "__main__":
    sys.exit(main())
