#!/usr/bin/env python3
"""Story status update script (Story 06-06).

Updates the status line in a story file header.

Usage: story_status.py <story-id> <new-status>

Valid status labels:
  - Planned
  - In Progress
  - Done
  - Done (QA PASS, <hash>)

Only touches the status line, preserves all other content.

Repo root is determined by traversing upward from the current working directory (CWD)
looking for a .git directory. This allows the script to work correctly when installed
centrally in ~/.config/opencode/scripts/ and called from any project directory.

Outputs JSON: {"story_id": "<id>", "old_status": "...", "new_status": "..."}

Exit codes:
  0 - success
  1 - story not found
  2 - invalid status label
"""

import json
import re
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Find repo root by traversing upward from cwd looking for .git directory.
    
    Returns the first directory containing a .git subdirectory, or falls back to
    the current working directory if no .git is found.
    """
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def find_story_file(repo_root: Path, story_id: str) -> Path | None:
    """Find story file by ID."""
    features_dir = repo_root / "docs" / "features"
    
    if not features_dir.exists():
        return None
    
    for feature_dir in features_dir.iterdir():
        if not feature_dir.is_dir() or feature_dir.name.startswith("_"):
            continue
        
        stories_dir = feature_dir / "stories"
        if not stories_dir.exists():
            continue
        
        for story_file in stories_dir.glob("*.md"):
            name = story_file.stem
            parts = name.split("-", 2)
            
            if len(parts) >= 2:
                file_id = f"{parts[0]}-{parts[1]}"
                if file_id == story_id:
                    return story_file
    
    return None


def is_valid_status(status: str) -> bool:
    """Check if status label is valid."""
    valid_labels = ["Planned", "In Progress", "Done"]
    
    # Check exact match
    if status in valid_labels:
        return True
    
    # Check "Done (QA PASS, <hash>)" format
    return bool(re.match(r"^Done \(QA PASS, [a-f0-9]+\)$", status))


def update_story_status(story_file: Path, new_status: str) -> tuple[int, str | None]:
    """Update story status line.
    
    Returns (exit_code, old_status or None)
    Exit codes: 0 success, 1 not found, 2 invalid status
    """
    if not story_file.exists():
        return 1, None
    
    if not is_valid_status(new_status):
        return 2, None
    
    try:
        content = story_file.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        
        old_status = None
        updated_lines = []
        
        for line in lines:
            if line.startswith("Status:"):
                old_status = line.split(":", 1)[1].strip()
                updated_lines.append(f"Status: {new_status}\n")
            else:
                updated_lines.append(line)
        
        if old_status is None:
            # No status line found
            return 1, None
        
        story_file.write_text("".join(updated_lines), encoding="utf-8")
        return 0, old_status
    except (OSError, ValueError):
        return 1, None


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: story_status.py <story-id> <new-status>"}), file=sys.stderr)
        return 1
    
    story_id = sys.argv[1]
    new_status = sys.argv[2]
    
    repo_root = get_repo_root()
    
    # Find story file
    story_file = find_story_file(repo_root, story_id)
    if not story_file:
        print(json.dumps({"error": f"Story not found: {story_id}"}), file=sys.stderr)
        return 1
    
    # Update status
    exit_code, old_status = update_story_status(story_file, new_status)
    
    if exit_code == 0:
        result = {
            "story_id": story_id,
            "old_status": old_status,
            "new_status": new_status,
        }
        print(json.dumps(result))
        return 0
    elif exit_code == 2:
        print(json.dumps({"error": f"Invalid status label: {new_status}"}), file=sys.stderr)
        return 2
    else:
        print(json.dumps({"error": f"Failed to update story: {story_id}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
