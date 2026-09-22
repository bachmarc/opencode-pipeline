#!/usr/bin/env python3
"""Story resolution script (Story 06-06).

Resolves a story from various input formats: story ID (06-01), slug (feature-hierarchy),
branch name (feature/06-01-feature-hierarchy), or partial match.

Outputs JSON with story metadata: id, slug, feature, branch, worktree, status, story_file.

Exit codes:
  0 - story found
  1 - story not found
  2 - ambiguous (multiple matches)
"""

import json
import sys
from pathlib import Path


def find_all_stories(repo_root: Path) -> list[dict]:
    """Find all stories in docs/features/*/stories/*.md."""
    stories = []
    features_dir = repo_root / "docs" / "features"
    
    if not features_dir.exists():
        return stories
    
    for feature_dir in features_dir.iterdir():
        if not feature_dir.is_dir() or feature_dir.name.startswith("_"):
            continue
        
        stories_dir = feature_dir / "stories"
        if not stories_dir.exists():
            continue
        
        # Extract feature slug from folder name (F-<ID>-<slug> or F-RETRO-retro)
        feature_slug = _extract_feature_slug(feature_dir.name)
        
        for story_file in stories_dir.glob("*.md"):
            # Parse filename: <phase>-<id>-<slug>.md
            name = story_file.stem
            parts = name.split("-", 2)
            
            if len(parts) < 3:
                continue
            
            phase = parts[0]
            story_id = f"{phase}-{parts[1]}"
            slug = parts[2]
            
            # Extract status from file
            try:
                content = story_file.read_text(encoding="utf-8")
                status = "Planned"  # default
                for line in content.splitlines():
                    if line.startswith("Status:"):
                        status = line.split(":", 1)[1].strip()
                        break
            except (OSError, ValueError):
                status = "Unknown"
            
            stories.append({
                "id": story_id,
                "slug": slug,
                "feature": feature_slug,
                "branch": f"feature/{story_id}-{slug}",
                "worktree": f".worktrees/{story_id}-{slug}",
                "status": status,
                "story_file": str(story_file.relative_to(repo_root)),
            })
    
    return stories


def _extract_feature_slug(folder_name: str) -> str:
    """Extract feature slug from folder name.
    
    Converts F-<ID>-<slug> to <slug>, or F-RETRO-retro to retro.
    """
    # Handle F-RETRO-retro case
    if folder_name == "F-RETRO-retro":
        return "retro"
    
    # Handle F-<ID>-<slug> case: split on first hyphen after F-
    if folder_name.startswith("F-"):
        # Remove F- prefix
        rest = folder_name[2:]
        # Find the next hyphen (after the ID)
        parts = rest.split("-", 1)
        if len(parts) == 2:
            return parts[1]
    
    # Fallback: return as-is
    return folder_name


def resolve_story(repo_root: Path, query: str) -> tuple[int, dict | None]:
    """Resolve a story from query string.
    
    Returns (exit_code, story_dict or None)
    Exit codes: 0 found, 1 not found, 2 ambiguous
    """
    stories = find_all_stories(repo_root)
    
    if not stories:
        return 1, None
    
    # Try exact matches first
    matches = []
    
    # Match by ID (e.g., "06-01")
    for story in stories:
        if story["id"] == query:
            matches.append(story)
    
    if len(matches) == 1:
        return 0, matches[0]
    elif len(matches) > 1:
        return 2, None
    
    # Match by slug (e.g., "feature-hierarchy")
    matches = []
    for story in stories:
        if story["slug"] == query:
            matches.append(story)
    
    if len(matches) == 1:
        return 0, matches[0]
    elif len(matches) > 1:
        return 2, None
    
    # Match by branch name (e.g., "feature/06-01-feature-hierarchy")
    matches = []
    for story in stories:
        if story["branch"] == query:
            matches.append(story)
    
    if len(matches) == 1:
        return 0, matches[0]
    elif len(matches) > 1:
        return 2, None
    
    # Match by partial ID (e.g., "01" matches "06-01")
    matches = []
    for story in stories:
        if query in story["id"]:
            matches.append(story)
    
    if len(matches) == 1:
        return 0, matches[0]
    elif len(matches) > 1:
        return 2, None
    
    # No match found
    return 1, None


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: resolve_story.py <query>"}), file=sys.stderr)
        return 1
    
    query = sys.argv[1]
    repo_root = Path(__file__).resolve().parent.parent
    
    exit_code, story = resolve_story(repo_root, query)
    
    if exit_code == 0 and story:
        print(json.dumps(story))
        return 0
    elif exit_code == 2:
        print(json.dumps({"error": "Ambiguous query"}), file=sys.stderr)
        return 2
    else:
        print(json.dumps({"error": "Story not found"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
