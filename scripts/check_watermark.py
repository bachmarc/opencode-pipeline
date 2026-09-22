#!/usr/bin/env python3
"""Check watermark in documentation files and report pending stories.

Reads the watermark from a given file (HTML comment format), compares it against
STORIES.md to find all done stories, and returns JSON with pending stories.

Exit code: 0 if up to date, 1 if stories are pending.
Accepts --file <path> argument. If no argument, checks both README.md and AGENTS.md.
"""

import argparse
import json
import re
import sys
from pathlib import Path


WATERMARK_PATTERN = r'<!-- synced_through: (\d{2}-\d{2}) \| updated: (\d{4}-\d{2}-\d{2}) -->'


def parse_watermark(file_path: Path) -> dict:
    """Parse watermark from file.
    
    Returns: {"synced_through": "14-01", "updated": "2026-09-22"} or None if not found
    """
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read {file_path}: {e}")
    
    if len(lines) < 2:
        return None
    
    line_2 = lines[1].strip()
    match = re.match(WATERMARK_PATTERN, line_2)
    
    if not match:
        return None
    
    return {
        "synced_through": match.group(1),
        "updated": match.group(2)
    }


def get_done_stories(stories_path: Path) -> list:
    """Extract all done story IDs from STORIES.md.
    
    Returns: list of story IDs (e.g., ["14-01", "15-01", ...])
    """
    try:
        with open(stories_path, "r") as f:
            content = f.read()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read {stories_path}: {e}")
    
    done_stories = []
    
    for line in content.split("\n"):
        # Look for lines with "Done" status
        if "| Done" in line or "| Done (" in line:
            # Extract story ID from the first column after |
            parts = line.split("|")
            if len(parts) >= 2:
                story_id = parts[1].strip()
                # Clean up story ID (remove markdown formatting like **)
                story_id = story_id.replace("**", "").strip()
                
                # Only add if it looks like a story ID (contains a dash)
                if story_id and "-" in story_id and story_id != "Story":
                    done_stories.append(story_id)
    
    return done_stories


def get_pending_stories(synced_through: str, done_stories: list) -> list:
    """Find stories that are done but after the synced_through story.
    
    Args:
        synced_through: Story ID like "14-01"
        done_stories: List of all done story IDs
    
    Returns: List of pending story IDs
    """
    if not synced_through or not done_stories:
        return []
    
    # Parse the synced_through story ID
    try:
        synced_phase, synced_num = synced_through.split("-")
        synced_phase = int(synced_phase)
        synced_num = int(synced_num)
    except (ValueError, AttributeError):
        return []
    
    pending = []
    
    for story_id in done_stories:
        try:
            phase, num = story_id.split("-")
            phase = int(phase)
            num = int(num)
        except (ValueError, AttributeError):
            continue
        
        # A story is pending if it's after the synced_through story
        if phase > synced_phase or (phase == synced_phase and num > synced_num):
            pending.append(story_id)
    
    return sorted(pending)


def check_file(file_path: Path, stories_path: Path) -> dict:
    """Check a single file and return results.
    
    Returns: {"file": "...", "synced_through": "14-01", "pending_stories": [...]}
    """
    watermark = parse_watermark(file_path)
    
    if not watermark:
        return {
            "file": str(file_path),
            "synced_through": None,
            "pending_stories": []
        }
    
    done_stories = get_done_stories(stories_path)
    pending = get_pending_stories(watermark["synced_through"], done_stories)
    
    return {
        "file": str(file_path),
        "synced_through": watermark["synced_through"],
        "pending_stories": pending
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check watermark in documentation files and report pending stories"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="File to check (relative to repo root). If not specified, checks both README.md and AGENTS.md"
    )
    
    args = parser.parse_args()
    
    # Determine repo root (where STORIES.md is)
    repo_root = Path(__file__).parent.parent
    stories_path = repo_root / "STORIES.md"
    
    if not stories_path.exists():
        print(json.dumps({"error": f"STORIES.md not found at {stories_path}"}))
        sys.exit(1)
    
    try:
        if args.file:
            # Check single file
            file_path = repo_root / args.file
            result = check_file(file_path, stories_path)
            print(json.dumps(result))
            
            # Exit with 1 if there are pending stories
            sys.exit(1 if result["pending_stories"] else 0)
        else:
            # Check both README.md and AGENTS.md
            results = []
            has_pending = False
            
            for filename in ["README.md", "AGENTS.md"]:
                file_path = repo_root / filename
                result = check_file(file_path, stories_path)
                results.append(result)
                
                if result["pending_stories"]:
                    has_pending = True
            
            # Print results as JSON array
            print(json.dumps(results))
            
            # Exit with 1 if any file has pending stories
            sys.exit(1 if has_pending else 0)
    
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
