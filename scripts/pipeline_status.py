#!/usr/bin/env python3
"""Pipeline status aggregation script.

Outputs machine-readable JSON of pipeline state:
- Features and their stories (from FEATURES.md and docs/features/*/feature.md)
- Git branches (feature/* branches mapped to stories)
- Worktrees (dirty/clean, last commit)
- QA state (from .pipeline/qa-state/*.json)
- Open intents (from .pipeline/intent.json)

Usage:
  pipeline_status.py              # Full status
  pipeline_status.py --feature <name>  # Filter to one feature
  pipeline_status.py --story <id>      # Filter to one story

Exit code: 0 always (status is informational, not pass/fail)
Output: JSON to stdout
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def get_repo_root() -> Path:
    """Find repo root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse YAML-like frontmatter from markdown file."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}
    
    meta: dict[str, Any] = {}
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        
        # Parse value types
        if value.lower() == "true":
            meta[key] = True
        elif value.lower() == "false":
            meta[key] = False
        elif value.startswith("[") and value.endswith("]"):
            # Parse list: [REQ-001, REQ-002]
            items = [item.strip() for item in value[1:-1].split(",")]
            meta[key] = items
        else:
            meta[key] = value
    
    return meta


def extract_status_from_body(text: str) -> str:
    """Extract status from markdown body (e.g., 'Status: done' or 'Status: Geplant')."""
    for line in text.splitlines():
        if line.startswith("Status:"):
            status_text = line.split(":", 1)[1].strip().lower()
            # Normalize status values
            if "done" in status_text or "fertig" in status_text:
                return "done"
            elif "progress" in status_text or "in-progress" in status_text or "laufend" in status_text:
                return "in-progress"
            elif "plan" in status_text or "geplant" in status_text:
                return "planned"
    return "unknown"


def read_features(repo_root: Path) -> list[dict[str, Any]]:
    """Read features from docs/features/*/feature.md files."""
    features: list[dict[str, Any]] = []
    features_dir = repo_root / "docs" / "features"
    
    if not features_dir.exists():
        return features
    
    for feature_dir in sorted(features_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        
        feature_file = feature_dir / "feature.md"
        if not feature_file.exists():
            continue
        
        text = feature_file.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        
        # Read stories for this feature
        stories: list[dict[str, Any]] = []
        stories_dir = feature_dir / "stories"
        if stories_dir.exists():
            for story_file in sorted(stories_dir.glob("*.md")):
                story_text = story_file.read_text(encoding="utf-8")
                story_meta = parse_frontmatter(story_text)
                
                # Extract story ID from filename (e.g., "06-05-pipeline-status.md" -> "06-05")
                match = re.match(r"(\d+-\d+)", story_file.stem)
                if match:
                    story_id = match.group(1)
                    story_meta["id"] = story_id
                    story_meta["filename"] = story_file.name
                    
                    # Extract status from markdown body if not in frontmatter
                    if "status" not in story_meta:
                        story_meta["status"] = extract_status_from_body(story_text)
                    
                    stories.append(story_meta)
        
        meta["stories"] = stories
        meta["feature_dir"] = feature_dir.name
        features.append(meta)
    
    return features


def get_git_branches(repo_root: Path) -> dict[str, str]:
    """Get all feature/* branches and their commit hashes."""
    branches: dict[str, str] = {}
    
    try:
        result = subprocess.run(
            ["git", "branch", "-a", "--format=%(refname:short) %(objectname:short)"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    branch_name = parts[0]
                    commit_hash = parts[1]
                    if branch_name.startswith("feature/"):
                        branches[branch_name] = commit_hash
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return branches


def get_worktrees(repo_root: Path) -> list[dict[str, Any]]:
    """Get worktree information."""
    worktrees: list[dict[str, Any]] = []
    worktrees_dir = repo_root / ".worktrees"
    
    if not worktrees_dir.exists():
        return worktrees
    
    for wt_dir in sorted(worktrees_dir.iterdir()):
        if not wt_dir.is_dir():
            continue
        
        wt_info: dict[str, Any] = {
            "path": wt_dir.name,
            "full_path": str(wt_dir),
        }
        
        # Get git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(wt_dir),
                capture_output=True,
                text=True,
                timeout=5,
            )
            wt_info["dirty"] = bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            wt_info["dirty"] = None
        
        # Get last commit
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H %s"],
                cwd=str(wt_dir),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(None, 1)
                wt_info["last_commit"] = parts[0][:7]
                wt_info["last_commit_msg"] = parts[1] if len(parts) > 1 else ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Get current branch
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(wt_dir),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                wt_info["branch"] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        worktrees.append(wt_info)
    
    return worktrees


def read_qa_state(repo_root: Path) -> dict[str, Any]:
    """Read QA state from .pipeline/qa-state/*.json files."""
    qa_state: dict[str, Any] = {}
    qa_dir = repo_root / ".pipeline" / "qa-state"
    
    if not qa_dir.exists():
        return qa_state
    
    for qa_file in sorted(qa_dir.glob("*.json")):
        try:
            data = json.loads(qa_file.read_text(encoding="utf-8"))
            qa_state[qa_file.stem] = data
        except (json.JSONDecodeError, OSError):
            pass
    
    return qa_state


def read_intents(repo_root: Path) -> list[dict[str, Any]]:
    """Read open intents from .pipeline/intent.json."""
    intents: list[dict[str, Any]] = []
    intent_file = repo_root / ".pipeline" / "intent.json"
    
    if not intent_file.exists():
        return intents
    
    try:
        data = json.loads(intent_file.read_text(encoding="utf-8"))
        intents = data.get("intents", [])
    except (json.JSONDecodeError, OSError):
        pass
    
    return intents


def derive_feature_status(stories: list[dict[str, Any]]) -> str:
    """Derive feature status from story statuses.
    
    - All stories done → feature done
    - Any story in-progress → feature in-progress
    - Any story planned → feature planned
    """
    if not stories:
        return "unknown"
    
    statuses = [s.get("status", "unknown") for s in stories]
    
    if "in-progress" in statuses:
        return "in-progress"
    if "planned" in statuses:
        return "planned"
    if all(s == "done" for s in statuses):
        return "done"
    
    return "unknown"


def build_status_json(
    features: list[dict[str, Any]],
    branches: dict[str, str],
    worktrees: list[dict[str, Any]],
    qa_state: dict[str, Any],
    intents: list[dict[str, Any]],
    feature_filter: str | None = None,
    story_filter: str | None = None,
) -> dict[str, Any]:
    """Build the complete status JSON object."""
    
    # Filter features if requested
    filtered_features = features
    if feature_filter:
        filtered_features = [
            f for f in features
            if f.get("feature_dir") == feature_filter or f.get("id") == feature_filter
        ]
    
    # Filter stories if requested
    if story_filter:
        filtered_features = [
            {
                **f,
                "stories": [s for s in f.get("stories", []) if story_filter in s.get("id", "")]
            }
            for f in filtered_features
        ]
    
    # Build feature list with derived status
    features_list = []
    all_stories = []
    
    for feature in filtered_features:
        stories = feature.get("stories", [])
        
        # Derive feature status from stories
        feature_status = derive_feature_status(stories)
        
        feature_obj = {
            "id": feature.get("id", "unknown"),
            "title": feature.get("title", ""),
            "status": feature_status,
            "owner": feature.get("owner", ""),
            "req": feature.get("req", []),  # Empty list if req: field is missing
            "story_count": len(stories),
        }
        
        features_list.append(feature_obj)
        all_stories.extend(stories)
    
    # Map branches to stories
    branch_mapping = {}
    for branch_name in branches:
        # Extract story ID from branch name (e.g., "feature/06-05-pipeline-status" -> "06-05")
        match = re.search(r"(\d+-\d+)", branch_name)
        if match:
            story_id = match.group(1)
            branch_mapping[branch_name] = story_id
    
    # Build output
    output: dict[str, Any] = {
        "features": features_list,
        "stories": all_stories,
        "branches": {
            "feature_branches": list(branches.keys()),
            "branch_mapping": branch_mapping,
        },
        "worktrees": worktrees,
        "qa_state": qa_state,
        "intents": intents,
    }
    
    return output


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Pipeline status aggregation script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--feature",
        type=str,
        help="Filter to one feature (by name or ID)",
    )
    parser.add_argument(
        "--story",
        type=str,
        help="Filter to one story (by ID, e.g., '06-05')",
    )
    
    args = parser.parse_args()
    
    repo_root = get_repo_root()
    
    # Collect data
    features = read_features(repo_root)
    branches = get_git_branches(repo_root)
    worktrees = get_worktrees(repo_root)
    qa_state = read_qa_state(repo_root)
    intents = read_intents(repo_root)
    
    # Build status JSON
    status = build_status_json(
        features,
        branches,
        worktrees,
        qa_state,
        intents,
        feature_filter=args.feature,
        story_filter=args.story,
    )
    
    # Output JSON
    print(json.dumps(status, indent=2))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
