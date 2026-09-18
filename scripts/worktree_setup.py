#!/usr/bin/env python3
"""Worktree setup script for deterministic branch/worktree creation (Story 06-04).

Subcommands:
  create <story-id>  — Create worktree and branch for a story
  remove <story-id>  — Remove worktree (after checking for uncommitted changes)
  list               — List all worktrees with branch and status

Uses only stdlib (pathlib, subprocess, json, argparse).

Exit codes:
  0 — success
  1 — story not found
  2 — main branch is dirty (for create)
  3 — worktree already exists (for create)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def find_story_file(story_id: str, repo_root: Path) -> Path | None:
    """Find story file by ID in docs/features/*/stories/ or docs/stories/.
    
    Returns: Path to story file, or None if not found.
    """
    # Try new hierarchy: docs/features/*/stories/<id>-*.md
    features_dir = repo_root / "docs" / "features"
    if features_dir.exists():
        for feature_dir in features_dir.iterdir():
            if feature_dir.is_dir() and feature_dir.name != "_story_template.md":
                stories_dir = feature_dir / "stories"
                if stories_dir.exists():
                    for story_file in stories_dir.glob(f"{story_id}-*.md"):
                        return story_file
    
    # Try backward compat: docs/stories/<id>-*.md
    stories_dir = repo_root / "docs" / "stories"
    if stories_dir.exists():
        for story_file in stories_dir.glob(f"{story_id}-*.md"):
            return story_file
    
    return None


def derive_slug(story_file: Path) -> str:
    """Derive slug from story filename.
    
    E.g., "06-04-worktree-setup.md" -> "worktree-setup"
    """
    # Remove .md extension
    name = story_file.stem
    
    # Remove story ID prefix (e.g., "06-04-")
    parts = name.split("-", 2)
    if len(parts) >= 3:
        # Format is <phase>-<id>-<slug>
        return "-".join(parts[2:])
    
    return name


def is_main_clean(repo_root: Path) -> bool:
    """Check if main branch is clean (no uncommitted changes)."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == ""


def worktree_exists(repo_root: Path, story_id: str, slug: str) -> bool:
    """Check if worktree already exists."""
    worktree_path = repo_root / ".worktrees" / f"{story_id}-{slug}"
    return worktree_path.exists()


def cmd_create(args: argparse.Namespace, repo_root: Path) -> int:
    """Create worktree and branch for a story.
    
    Returns: 0 on success, 1 if story not found, 2 if main is dirty, 3 if worktree exists.
    """
    story_id = args.story_id
    
    # Find story file
    story_file = find_story_file(story_id, repo_root)
    if story_file is None:
        output = {
            "error": "story_not_found",
            "message": f"Story {story_id} not found in docs/features/*/stories/ or docs/stories/",
        }
        print(json.dumps(output))
        return 1
    
    # Derive slug
    slug = derive_slug(story_file)
    
    # Check if worktree already exists
    if worktree_exists(repo_root, story_id, slug):
        output = {
            "error": "worktree_exists",
            "message": f"Worktree for {story_id}-{slug} already exists",
        }
        print(json.dumps(output))
        return 3
    
    # Check if main is clean
    if not is_main_clean(repo_root):
        output = {
            "error": "main_dirty",
            "message": "Main branch has uncommitted changes",
        }
        print(json.dumps(output))
        return 2
    
    # Create worktree directory
    worktree_path = repo_root / ".worktrees" / f"{story_id}-{slug}"
    worktree_path.mkdir(parents=True, exist_ok=True)
    
    # Create branch name
    branch_name = f"feature/{story_id}-{slug}"
    
    # Create git worktree
    result = subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode != 0:
        output = {
            "error": "worktree_creation_failed",
            "message": f"Failed to create git worktree: {result.stderr}",
        }
        print(json.dumps(output))
        return 1
    
    # Output success JSON
    output = {
        "worktree": str(worktree_path.relative_to(repo_root)),
        "branch": branch_name,
        "story_file": str(story_file.relative_to(repo_root)),
    }
    print(json.dumps(output))
    return 0


def cmd_remove(args: argparse.Namespace, repo_root: Path) -> int:
    """Remove worktree after checking for uncommitted changes.
    
    Returns: 0 on success, 1 on error.
    """
    story_id = args.story_id
    
    # Find story file to get slug
    story_file = find_story_file(story_id, repo_root)
    if story_file is None:
        output = {
            "error": "story_not_found",
            "message": f"Story {story_id} not found",
        }
        print(json.dumps(output))
        return 1
    
    slug = derive_slug(story_file)
    worktree_path = repo_root / ".worktrees" / f"{story_id}-{slug}"
    
    if not worktree_path.exists():
        output = {
            "error": "worktree_not_found",
            "message": f"Worktree {worktree_path} does not exist",
        }
        print(json.dumps(output))
        return 1
    
    # Check for uncommitted changes in worktree
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(worktree_path),
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode == 0 and result.stdout.strip() != "":
        output = {
            "error": "worktree_dirty",
            "message": "Worktree has uncommitted changes",
        }
        print(json.dumps(output))
        return 1
    
    # Remove git worktree
    result = subprocess.run(
        ["git", "worktree", "remove", str(worktree_path)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode != 0:
        output = {
            "error": "worktree_removal_failed",
            "message": f"Failed to remove git worktree: {result.stderr}",
        }
        print(json.dumps(output))
        return 1
    
    # Output success JSON
    output = {
        "removed": True,
        "path": str(worktree_path.relative_to(repo_root)),
    }
    print(json.dumps(output))
    return 0


def cmd_list(args: argparse.Namespace, repo_root: Path) -> int:
    """List all worktrees with branch and status.
    
    Returns: 0 on success.
    """
    # Get list of worktrees from git
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    
    worktrees = []
    
    if result.returncode == 0 and result.stdout.strip():
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            
            # Parse worktree line: "worktree <path>"
            parts = line.split()
            if len(parts) >= 2 and parts[0] == "worktree":
                path = parts[1]
                path_obj = Path(path)
                
                # Skip if not in .worktrees directory
                if ".worktrees" not in path_obj.parts:
                    continue
                
                # Get branch name
                branch = "unknown"
                result_branch = subprocess.run(
                    ["git", "symbolic-ref", "--short", "HEAD"],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result_branch.returncode == 0:
                    branch = result_branch.stdout.strip()
                
                # Get status
                result_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                status = "clean" if result_status.returncode == 0 and not result_status.stdout.strip() else "dirty"
                
                worktrees.append({
                    "path": str(Path(path).relative_to(repo_root)),
                    "branch": branch,
                    "status": status,
                })
    
    # Output JSON array
    print(json.dumps(worktrees))
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deterministic worktree and branch setup",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # create subcommand
    create_parser = subparsers.add_parser("create", help="Create worktree for a story")
    create_parser.add_argument("story_id", help="Story ID (e.g., 06-04)")
    
    # remove subcommand
    remove_parser = subparsers.add_parser("remove", help="Remove a worktree")
    remove_parser.add_argument("story_id", help="Story ID (e.g., 06-04)")
    
    # list subcommand
    subparsers.add_parser("list", help="List all worktrees")
    
    args = parser.parse_args()
    
    # Get repo root (current directory)
    repo_root = Path.cwd()
    
    # Dispatch to command handler
    if args.command == "create":
        return cmd_create(args, repo_root)
    elif args.command == "remove":
        return cmd_remove(args, repo_root)
    elif args.command == "list":
        return cmd_list(args, repo_root)
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
