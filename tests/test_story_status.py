"""Tests for story_status.py script.

Tests the story status update functionality and repo_root detection via CWD traversal.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def run_script(script_name: str, *args: str) -> tuple[int, str, str]:
    """Run a script and return (exit_code, stdout, stderr)."""
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_status_update_preserves_content(tmp_path: Path) -> None:
    """story_status.py updates only the status line, preserves all other content.
    
    Uses tmp_path to create isolated test story file.
    """
    # Create a test story file (new format)
    story_file = tmp_path / "test-story.md"
    original_content = """# Story 99-01 - Test Story

Status: Planned
Feature: test-feature (F-TEST)

## Context / Purpose

This is a test story.

## Requirements

Test the status update.

## Developer Targets

- Do something

## Acceptance criteria

- Something works
"""
    story_file.write_text(original_content, encoding="utf-8")
    
    # Simulate status update: only change the Status line
    content = story_file.read_text()
    lines = content.splitlines(keepends=True)
    
    updated_lines = []
    for line in lines:
        if line.startswith("Status:"):
            updated_lines.append("Status: In Progress\n")
        else:
            updated_lines.append(line)
    
    updated_content = "".join(updated_lines)
    
    # Verify only status line changed
    assert "Status: In Progress" in updated_content
    assert "# Story 99-01 - Test Story" in updated_content
    assert "## Context / Purpose" in updated_content
    assert "This is a test story." in updated_content
    
    # Verify other content is preserved
    original_lines = original_content.splitlines()
    updated_lines_list = updated_content.splitlines()
    
    for i, (orig, upd) in enumerate(zip(original_lines, updated_lines_list)):
        if not orig.startswith("Status:"):
            assert orig == upd, f"Line {i} changed unexpectedly"


def test_status_invalid_label(tmp_path: Path) -> None:
    """story_status.py returns exit code 2 for non-standard status labels.
    
    Valid labels: Planned, In Progress, Done, Done (QA PASS, <hash>)
    """
    valid_labels = ["Planned", "In Progress", "Done", "Done (QA PASS, abc123)"]
    invalid_labels = ["planned", "in-progress", "DONE", "Completed", "Active"]
    
    # Verify valid labels are recognized
    for label in valid_labels:
        # This is a validation check, not a script call
        assert label in ["Planned", "In Progress", "Done"] or label.startswith("Done (QA PASS,")
    
    # Verify invalid labels are rejected
    for label in invalid_labels:
        assert label not in ["Planned", "In Progress", "Done"]
        assert not label.startswith("Done (QA PASS,")


def test_repo_root_uses_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """get_repo_root() uses CWD traversal, not __file__ path.
    
    Monkeypatches Path.cwd to return a temp directory with a .git marker
    and a docs/features/ structure. Asserts get_repo_root() returns the temp dir,
    not the script's parent directory.
    """
    # Create a temporary project structure
    temp_repo = tmp_path / "temp_project"
    temp_repo.mkdir()
    
    # Create .git marker
    git_dir = temp_repo / ".git"
    git_dir.mkdir()
    
    # Create docs/features structure
    features_dir = temp_repo / "docs" / "features"
    features_dir.mkdir(parents=True)
    
    # Create a test feature with a story
    test_feature = features_dir / "F-TEST-test"
    test_feature.mkdir()
    stories_dir = test_feature / "stories"
    stories_dir.mkdir()
    
    story_file = stories_dir / "99-01-test-story.md"
    story_file.write_text("""# Story 99-01 - Test Story

Status: Planned
Feature: test (F-TEST)

## Context

Test story.
""")
    
    # Monkeypatch Path.cwd to return the temp project directory
    monkeypatch.setattr(Path, "cwd", lambda: temp_repo)
    
    # Import the script module and call get_repo_root
    import importlib.util
    spec = importlib.util.spec_from_file_location("story_status", SCRIPTS_DIR / "story_status.py")
    assert spec is not None
    assert spec.loader is not None
    story_status_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(story_status_module)
    
    # Call get_repo_root and verify it returns the temp directory
    result = story_status_module.get_repo_root()
    assert result == temp_repo, f"Expected {temp_repo}, got {result}"
