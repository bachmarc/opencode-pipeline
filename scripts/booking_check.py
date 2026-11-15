#!/usr/bin/env python3
"""Booking check: verify story status claims against git ancestry (Story 33-02).

Scans all story files for Status: Done* lines containing a commit SHA reference
and verifies that each SHA is an ancestor of HEAD. Reports booking-vs-git
divergence violations.

Used by session_recovery.py to surface violations at session start.

CLI: python scripts/booking_check.py
  - Exits 0 when all claimed-done SHAs are ancestors (clean)
  - Exits 1 when divergence is found (violations exist)
  - Prints human-readable output to stdout, one violation per line

Module docstring documents the purpose and exit codes.
Uses only stdlib + git subprocess. No external dependencies.
"""

import re
import subprocess
import sys
from pathlib import Path


def scan_done_statuses(repo_root: str) -> list[dict]:
    """Scan all story files for Status: Done* lines with SHA references.
    
    Pattern: matches `Status: Done*` lines containing 7+ hex characters,
    extracting the SHA.
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        List of dicts: {"story_file": str, "sha": str, "status_line": str}
    """
    results = []
    repo_path = Path(repo_root)
    
    # Find all story files in docs/features/*/stories/
    features_dir = repo_path / "docs" / "features"
    if not features_dir.exists():
        return results
    
    for story_file in features_dir.glob("*/stories/*.md"):
        try:
            content = story_file.read_text(encoding="utf-8")
            
            # Find Status: Done* lines
            for line in content.split("\n"):
                # Pattern: Status: Done followed by anything containing 7+ hex chars
                if line.startswith("Status:") and "Done" in line:
                    # Extract SHA: 7+ consecutive hex characters
                    sha_match = re.search(r"\b([0-9a-fA-F]{7,})\b", line)
                    if sha_match:
                        sha = sha_match.group(1)
                        results.append({
                            "story_file": str(story_file.relative_to(repo_path)),
                            "sha": sha,
                            "status_line": line.strip(),
                        })
        except (OSError, UnicodeDecodeError):
            pass
    
    return results


def check_ancestry(sha: str, repo_root: str) -> bool:
    """Check if a SHA is an ancestor of HEAD.
    
    Runs: git merge-base --is-ancestor <sha> HEAD
    
    Args:
        sha: Commit SHA to check
        repo_root: Root directory of the repository
        
    Returns:
        True if the SHA is an ancestor of HEAD, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        # git not found
        return False


def run(repo_root: str) -> list[dict]:
    """Scan story files and check all claimed-done SHAs against git ancestry.
    
    Returns violations: SHAs that are NOT ancestors of HEAD.
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        List of dicts: {"story_file": str, "sha": str}
        Empty list if no violations (all SHAs are ancestors)
    """
    violations = []
    
    # Scan for all Done* statuses with SHAs
    done_statuses = scan_done_statuses(repo_root)
    
    # Check each SHA
    for status in done_statuses:
        sha = status["sha"]
        if not check_ancestry(sha, repo_root):
            violations.append({
                "story_file": status["story_file"],
                "sha": sha,
            })
    
    return violations


def main() -> int:
    """CLI entry point.
    
    Exits 0 when clean (no violations).
    Exits 1 when violations found.
    Prints human-readable output to stdout.
    """
    repo_root = Path.cwd()
    
    violations = run(str(repo_root))
    
    if violations:
        # Print violations
        for v in violations:
            print(f"Booking divergence: {v['story_file']} references SHA {v['sha']}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
