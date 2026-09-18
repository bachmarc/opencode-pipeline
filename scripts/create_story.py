#!/usr/bin/env python3
"""Story creation script (Story 06-06).

Creates a new story from template for a given feature.

Usage: create_story.py <feature-name> <slug> [--feature <feature-id>]

Determines next free ID for the feature's phase, copies _story_template.md,
fills machine fields (ID, Feature, status=Planned), and adds entry to feature.md.

Outputs JSON: {"story_file": "<path>", "id": "<id>"}

Exit codes:
  0 - success
  1 - feature not found
  2 - template missing
"""

import argparse
import json
import shutil
import sys
from pathlib import Path


def get_next_story_id(feature_dir: Path) -> str | None:
    """Determine next free ID for the feature's phase.
    
    Reads existing story files and returns next available ID.
    Returns None if unable to determine.
    """
    stories_dir = feature_dir / "stories"
    if not stories_dir.exists():
        return None
    
    # Find all existing story IDs in this feature
    existing_ids = []
    for story_file in stories_dir.glob("*.md"):
        name = story_file.stem
        parts = name.split("-", 2)
        if len(parts) >= 2:
            try:
                phase = int(parts[0])
                story_num = int(parts[1])
                existing_ids.append((phase, story_num))
            except ValueError:
                continue
    
    if not existing_ids:
        # No existing stories, start with phase 1, ID 1
        return "01-01"
    
    # Find the phase (should be consistent within a feature)
    phases = {p for p, _ in existing_ids}
    if len(phases) != 1:
        # Multiple phases in same feature - use the first one
        phase = min(phases)
    else:
        phase = phases.pop()
    
    # Find next ID within this phase
    phase_ids = [story_num for p, story_num in existing_ids if p == phase]
    next_id = max(phase_ids) + 1 if phase_ids else 1
    
    return f"{phase:02d}-{next_id:02d}"


def add_story_to_feature_md(feature_md: Path, story_id: str, slug: str) -> bool:
    """Add story entry to feature.md Stories list.
    
    Returns True on success, False on error.
    """
    try:
        content = feature_md.read_text(encoding="utf-8")
        
        # Find the Stories section
        lines = content.splitlines(keepends=True)
        insert_idx = None
        
        for i, line in enumerate(lines):
            if line.strip() == "## Stories":
                # Find the next line after "## Stories"
                insert_idx = i + 1
                break
        
        if insert_idx is None:
            return False
        
        # Insert the new story entry
        new_entry = f"- {story_id}-{slug} (planned)\n"
        lines.insert(insert_idx + 1, new_entry)
        
        feature_md.write_text("".join(lines), encoding="utf-8")
        return True
    except (OSError, ValueError):
        return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create a new story from template")
    parser.add_argument("feature_name", help="Feature name (e.g., 'pipeline-evolution')")
    parser.add_argument("slug", help="Story slug (e.g., 'my-story')")
    parser.add_argument("--feature", required=False, help="Feature ID (e.g., 'F-001') to fill Feature: line")
    parser.add_argument("--req", required=False, help="(Deprecated) REQ-ID parameter, ignored")
    
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parent.parent
    features_dir = repo_root / "docs" / "features"
    
    # Check if feature exists
    feature_dir = features_dir / args.feature_name
    if not feature_dir.exists():
        print(json.dumps({"error": f"Feature not found: {args.feature_name}"}), file=sys.stderr)
        return 1
    
    # Check if template exists
    template_file = features_dir / "_story_template.md"
    if not template_file.exists():
        print(json.dumps({"error": "Template file not found"}), file=sys.stderr)
        return 2
    
    # Determine next story ID
    next_id = get_next_story_id(feature_dir)
    if not next_id:
        print(json.dumps({"error": "Unable to determine next story ID"}), file=sys.stderr)
        return 1
    
    # Create stories directory if needed
    stories_dir = feature_dir / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy template to new story file
    story_filename = f"{next_id}-{args.slug}.md"
    story_file = stories_dir / story_filename
    
    try:
        shutil.copy(str(template_file), str(story_file))
    except OSError as e:
        print(json.dumps({"error": f"Failed to copy template: {e}"}), file=sys.stderr)
        return 1
    
    # Fill in machine fields in the new story file
    try:
        content = story_file.read_text(encoding="utf-8")
        
        # Replace placeholders
        content = content.replace("<ID>", next_id)
        content = content.replace("<Title>", args.slug.replace("-", " ").title())
        
        # Fill Feature: line if --feature is provided
        if args.feature:
            content = content.replace("<feature-name> (<feature-id>)", f"{args.feature_name} ({args.feature})")
        else:
            # Just fill with feature name if no feature ID provided
            content = content.replace("<feature-name> (<feature-id>)", args.feature_name)
        
        # Ensure status is "Planned"
        lines = content.splitlines(keepends=True)
        updated_lines = []
        for line in lines:
            if line.startswith("Status:"):
                updated_lines.append("Status: Planned\n")
            else:
                updated_lines.append(line)
        
        content = "".join(updated_lines)
        story_file.write_text(content, encoding="utf-8")
    except (OSError, ValueError) as e:
        print(json.dumps({"error": f"Failed to update story file: {e}"}), file=sys.stderr)
        return 1
    
    # Add entry to feature.md
    feature_md = feature_dir / "feature.md"
    if not add_story_to_feature_md(feature_md, next_id, args.slug):
        print(json.dumps({"error": "Failed to update feature.md"}), file=sys.stderr)
        return 1
    
    # Output success
    result = {
        "story_file": str(story_file.relative_to(repo_root)),
        "id": next_id,
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
