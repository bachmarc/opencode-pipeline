#!/usr/bin/env python3
"""Retro story generator script (Story 12-05, extended in 25-03).

Creates retro feature and story files from a JSON definition.
Used during project migration to document pre-pipeline development.
Retro feature folder uses F-RETRO-retro naming convention.

Story 25-03 extends this script with:
1. scan_history() - analyzes git history and documentation (CHANGELOG.md, TODO.md, README.md)
   to inform the Phase 5 migration dialog about the project's existing history.
2. create_baseline_story() - creates a single baseline story covering all pre-pipeline work,
   useful for large legacy codebases where granular reconstruction is impractical.

History handling strategies:
1. Granular retro stories - analyze git + docs and generate one done story per milestone
2. Baseline story - single 00-00-baseline-existing-state.md covering everything before pipeline
3. Clean start - ignore history, pipeline adoption is the starting point (no retro stories)

Usage: create_retro_stories.py <target_path> <retro_definition.json>

Input JSON format:
{
  "feature_id": "F-RETRO",
  "feature_title": "Pre-Pipeline Development",
  "stories": [
    {"id": "RETRO-01", "slug": "initial-development", "title": "Initial Development", "summary": "..."}
  ]
}

Output: JSON with {"created": [...], "skipped": [...], "updated": [...]}

Exit codes:
  0 - success
  1 - path doesn't exist
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def scan_history(target: Path) -> dict:
    """Scan project history from git and documentation files.
    
    Collects information about pre-pipeline development from multiple sources:
    - Git history (commits, date range, messages)
    - CHANGELOG.md entries (version headings)
    - TODO.md items (outstanding work)
    - README.md history section (if present)
    
    This is used by the Phase 5 migrate dialog to inform the user about existing
    work and help them choose a history handling strategy (granular retro stories,
    baseline story, or clean start).
    
    Args:
        target: Path to project root
        
    Returns:
        Dictionary with keys:
        - git_summary: {commits: int, date_range: [first, last], messages: [str]}
        - changelog_entries: list of version heading strings (e.g., ["## v1.2.0", ...])
        - todo_items: list of non-empty lines from TODO.md
        - readme_history_section: content of ## History or ## Changelog section in README
    """
    result = {
        "git_summary": {
            "commits": 0,
            "date_range": [],
            "messages": []
        },
        "changelog_entries": [],
        "todo_items": [],
        "readme_history_section": ""
    }
    
    # Scan git history
    git_dir = target / ".git"
    if git_dir.exists():
        try:
            # Get commit count
            count_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=target,
                capture_output=True,
                text=True,
                timeout=5
            )
            if count_result.returncode == 0:
                result["git_summary"]["commits"] = int(count_result.stdout.strip())
            
            # Get first and last commit dates
            if result["git_summary"]["commits"] > 0:
                # Get first commit date
                first_result = subprocess.run(
                    ["git", "log", "--format=%aI", "--reverse"],
                    cwd=target,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if first_result.returncode == 0 and first_result.stdout.strip():
                    first_date = first_result.stdout.strip().split('\n')[0]
                    
                    # Get last commit date
                    last_result = subprocess.run(
                        ["git", "log", "-1", "--format=%aI"],
                        cwd=target,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if last_result.returncode == 0:
                        last_date = last_result.stdout.strip()
                        result["git_summary"]["date_range"] = [first_date, last_date]
                
                # Get last 10 commit messages
                msg_result = subprocess.run(
                    ["git", "log", "-10", "--format=%s"],
                    cwd=target,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if msg_result.returncode == 0:
                    messages = [msg.strip() for msg in msg_result.stdout.strip().split('\n') if msg.strip()]
                    result["git_summary"]["messages"] = messages
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            # Git not available or error occurred, leave git_summary empty
            pass
    
    # Scan CHANGELOG.md for version headings
    changelog = target / "CHANGELOG.md"
    if changelog.exists():
        try:
            content = changelog.read_text(encoding="utf-8")
            lines = content.split('\n')
            for line in lines:
                # Look for markdown headings (##, ###, etc.)
                if line.startswith('#') and '##' in line:
                    stripped = line.strip()
                    if stripped:
                        result["changelog_entries"].append(stripped)
        except Exception:
            pass
    
    # Scan TODO.md for items
    todo = target / "TODO.md"
    if todo.exists():
        try:
            content = todo.read_text(encoding="utf-8")
            lines = content.split('\n')
            for line in lines:
                # Include non-empty lines (skip the title line "# TODO")
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    result["todo_items"].append(stripped)
        except Exception:
            pass
    
    # Scan README.md for History section
    readme = target / "README.md"
    if readme.exists():
        try:
            content = readme.read_text(encoding="utf-8")
            lines = content.split('\n')
            
            # Look for ## History or ## Changelog section
            in_history = False
            history_lines = []
            for i, line in enumerate(lines):
                if line.startswith('## ') and ('History' in line or 'Changelog' in line):
                    in_history = True
                    continue
                elif in_history:
                    # Stop at the next top-level heading
                    if line.startswith('## ') or line.startswith('# '):
                        break
                    history_lines.append(line)
            
            if history_lines:
                result["readme_history_section"] = '\n'.join(history_lines).strip()
        except Exception:
            pass
    
    return result


def create_baseline_story(target: Path, summary: str) -> dict:
    """Create a single baseline story covering all pre-pipeline development.
    
    Creates a single `00-00-baseline-existing-state.md` story marked as Done,
    useful for large legacy codebases where granular reconstruction is impractical.
    
    Args:
        target: Path to project root
        summary: Descriptive text about the baseline work
        
    Returns:
        Dictionary with "created" or "skipped" lists
    """
    result = {
        "created": [],
        "skipped": []
    }
    
    # Create feature directory structure
    features_dir = target / "docs" / "features" / "F-RETRO-retro"
    stories_dir = features_dir / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    
    baseline_file = stories_dir / "00-00-baseline-existing-state.md"
    
    if baseline_file.exists():
        result["skipped"].append(str(baseline_file))
        return result
    
    # Create baseline story content
    content = f"""# Story 00-00-baseline-existing-state

Status: Done
Feature: F-RETRO-retro

## Context / Purpose

Baseline snapshot of all development prior to pipeline adoption. Captures the existing state of the project before implementing the opencode pipeline framework.

## Summary

{summary}

## Requirements

Retroactive documentation — no implementation required.

## Developer Targets (exactly, no more / no less)

- Retroactive: no targets (pre-existing work)

## Acceptance criteria (checked by qa-manager)

- Retroactive documentation only

## Test criteria (must exist BEFORE implementation)

- Retroactive: no test criteria
"""
    
    baseline_file.write_text(content, encoding="utf-8")
    result["created"].append(str(baseline_file))
    
    return result


def create_retro_stories(target_path: str, retro_def: dict) -> dict:
    """Create retro feature and story files.
    
    Args:
        target_path: Path to project root where docs/ will be created
        retro_def: Dictionary with feature_id, feature_title, and stories list
        
    Returns:
        Dictionary with "created", "skipped", and "updated" lists
    """
    target = Path(target_path)
    
    if not target.exists():
        raise ValueError(f"Target path does not exist: {target}")
    
    result = {
        "created": [],
        "skipped": [],
        "updated": []
    }
    
    # Create feature directory structure
    features_dir = target / "docs" / "features" / "F-RETRO-retro"
    stories_dir = features_dir / "stories"
    
    # Create directories
    features_dir.mkdir(parents=True, exist_ok=True)
    stories_dir.mkdir(parents=True, exist_ok=True)
    
    # Create feature.md
    feature_md_path = features_dir / "feature.md"
    if not feature_md_path.exists():
        feature_md_content = _generate_feature_md(retro_def)
        feature_md_path.write_text(feature_md_content, encoding="utf-8")
        result["created"].append(str(feature_md_path))
    
    # Create story files
    for story in retro_def.get("stories", []):
        story_id = story["id"]
        slug = story["slug"]
        title = story["title"]
        summary = story["summary"]
        
        story_file = stories_dir / f"{story_id}-{slug}.md"
        
        if story_file.exists():
            result["skipped"].append(str(story_file))
        else:
            story_content = _generate_story_md(story_id, title, summary, retro_def["feature_id"])
            story_file.write_text(story_content, encoding="utf-8")
            result["created"].append(str(story_file))
    
    # Update or create FEATURES.md
    features_index = target / "FEATURES.md"
    if features_index.exists():
        _append_to_features_md(features_index, retro_def)
        result["updated"].append(str(features_index))
    else:
        _create_features_md(features_index, retro_def)
        result["created"].append(str(features_index))
    
    # Update or create STORIES.md
    stories_index = target / "STORIES.md"
    if stories_index.exists():
        _append_to_stories_md(stories_index, retro_def)
        result["updated"].append(str(stories_index))
    else:
        _create_stories_md(stories_index, retro_def)
        result["created"].append(str(stories_index))
    
    return result


def _generate_feature_md(retro_def: dict) -> str:
    """Generate feature.md content."""
    feature_id = retro_def["feature_id"]
    feature_title = retro_def["feature_title"]
    
    # Build stories list
    stories_list = []
    for story in retro_def.get("stories", []):
        story_id = story["id"]
        stories_list.append(f"- {story_id} (done)")
    
    stories_section = "\n".join(stories_list)
    
    content = f"""---
id: {feature_id}
title: {feature_title}
status: done
owner: ""
---

## Vision

Retroactive documentation of pre-pipeline development.

## Context

{feature_title}

## Stories

{stories_section}
"""
    return content


def _generate_story_md(story_id: str, title: str, summary: str, feature_id: str) -> str:
    """Generate story.md content."""
    content = f"""# Story {story_id} — {title}

Status: Retro-Done
Feature: F-RETRO-retro ({feature_id})

## Context / Purpose

{summary}

## Requirements

Retroactive documentation — no implementation required.

## Developer Targets (exactly, no more / no less)

- Retroactive: no targets (pre-existing work)

## Acceptance criteria (checked by qa-manager)

- Retroactive documentation only

## Test criteria (must exist BEFORE implementation)

- Retroactive: no test criteria
"""
    return content


def _append_to_features_md(features_md: Path, retro_def: dict) -> None:
    """Append retro feature entry to existing FEATURES.md."""
    content = features_md.read_text(encoding="utf-8")
    
    # Check if F-RETRO already exists
    if retro_def["feature_id"] in content:
        return
    
    # Find the last table row and append after it
    lines = content.splitlines(keepends=True)
    
    # Build the new row
    feature_id = retro_def["feature_id"]
    feature_title = retro_def["feature_title"]
    stories = ", ".join(s["id"] for s in retro_def.get("stories", []))
    
    new_row = f"| {feature_id} | {feature_title} | done | — | {stories} |\n"
    
    # Find the last table row (skip header and separator)
    last_table_row_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith("|") and "---" not in lines[i]:
            last_table_row_idx = i
            break
    
    if last_table_row_idx >= 0:
        lines.insert(last_table_row_idx + 1, new_row)
    else:
        # Fallback: append at end
        lines.append(new_row)
    
    features_md.write_text("".join(lines), encoding="utf-8")


def _create_features_md(features_md: Path, retro_def: dict) -> None:
    """Create FEATURES.md with retro entry."""
    feature_id = retro_def["feature_id"]
    feature_title = retro_def["feature_title"]
    stories = ", ".join(s["id"] for s in retro_def.get("stories", []))
    
    content = f"""# FEATURES.md

Top-level index of features and their stories.

| Feature | Title | Status | Owner | Stories |
|---------|-------|--------|-------|---------|
| {feature_id} | {feature_title} | done | — | {stories} |
"""
    features_md.write_text(content, encoding="utf-8")


def _append_to_stories_md(stories_md: Path, retro_def: dict) -> None:
    """Append retro story entries to existing STORIES.md."""
    content = stories_md.read_text(encoding="utf-8")
    
    # Check if any RETRO story already exists
    if any(s["id"] in content for s in retro_def.get("stories", [])):
        return
    
    lines = content.splitlines(keepends=True)
    
    # Find the last table row and append after it
    last_table_row_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith("|") and "---" not in lines[i]:
            last_table_row_idx = i
            break
    
    # Build new rows
    feature_id = retro_def["feature_id"]
    new_rows = []
    for story in retro_def.get("stories", []):
        story_id = story["id"]
        title = story["title"]
        new_row = f"| {story_id} | {title} | Retro-Done | {feature_id} retro |\n"
        new_rows.append(new_row)
    
    if last_table_row_idx >= 0:
        for i, row in enumerate(new_rows):
            lines.insert(last_table_row_idx + 1 + i, row)
    else:
        # Fallback: append at end
        lines.extend(new_rows)
    
    stories_md.write_text("".join(lines), encoding="utf-8")


def _create_stories_md(stories_md: Path, retro_def: dict) -> None:
    """Create STORIES.md with retro entries."""
    feature_id = retro_def["feature_id"]
    
    # Build story rows
    story_rows = []
    for story in retro_def.get("stories", []):
        story_id = story["id"]
        title = story["title"]
        story_rows.append(f"| {story_id} | {title} | Retro-Done | {feature_id} retro |")
    
    stories_section = "\n".join(story_rows)
    
    content = f"""# STORIES.md

Index and status per story.

| Story | Title | Status | Traceability |
|---|---|---|---|
{stories_section}
"""
    stories_md.write_text(content, encoding="utf-8")


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Create retro feature and story files from JSON definition"
    )
    parser.add_argument("target_path", help="Target project path")
    parser.add_argument("retro_definition", help="Path to retro definition JSON file")
    
    args = parser.parse_args()
    
    # Load JSON definition
    try:
        with open(args.retro_definition, "r", encoding="utf-8") as f:
            retro_def = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading retro definition: {e}", file=sys.stderr)
        return 1
    
    # Create retro stories
    try:
        result = create_retro_stories(args.target_path, retro_def)
        print(json.dumps(result, indent=2))
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
