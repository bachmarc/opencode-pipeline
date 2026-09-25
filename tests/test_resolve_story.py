"""Tests for resolve_story.py script.

Tests the story resolution functionality and repo_root detection via CWD traversal.
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


def test_resolve_by_id() -> None:
    """resolve_story.py resolves story by ID (e.g., '06-01')."""
    exit_code, stdout, stderr = run_script("resolve_story.py", "06-01")
    
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}. stderr: {stderr}"
    
    data = json.loads(stdout)
    assert data["id"] == "06-01"
    assert data["slug"] == "feature-hierarchy"
    assert data["feature"] == "pipeline-evolution"
    assert data["branch"] == "feature/06-01-feature-hierarchy"
    assert data["worktree"] == ".worktrees/06-01-feature-hierarchy"
    assert "story_file" in data


def test_resolve_by_branch() -> None:
    """resolve_story.py resolves story by branch name (e.g., 'feature/06-01-feature-hierarchy')."""
    exit_code, stdout, stderr = run_script("resolve_story.py", "feature/06-01-feature-hierarchy")
    
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}. stderr: {stderr}"
    
    data = json.loads(stdout)
    assert data["id"] == "06-01"
    assert data["slug"] == "feature-hierarchy"
    assert data["branch"] == "feature/06-01-feature-hierarchy"


def test_resolve_not_found() -> None:
    """resolve_story.py returns exit code 1 for unknown story."""
    exit_code, stdout, stderr = run_script("resolve_story.py", "99-99")
    
    assert exit_code == 1, f"Expected exit code 1 for not found, got {exit_code}"


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
    spec = importlib.util.spec_from_file_location("resolve_story", SCRIPTS_DIR / "resolve_story.py")
    assert spec is not None
    assert spec.loader is not None
    resolve_story_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(resolve_story_module)
    
    # Call get_repo_root and verify it returns the temp directory
    result = resolve_story_module.get_repo_root()
    assert result == temp_repo, f"Expected {temp_repo}, got {result}"
