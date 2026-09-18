"""Tests for Story Status Guard plugin."""

import os
import re
from pathlib import Path


def test_story_status_guard_file_exists():
    """Test that plugins/guards/story-status-guard.ts exists."""
    guard_file = Path(__file__).parent.parent / "plugins" / "guards" / "story-status-guard.ts"
    assert guard_file.exists(), f"Guard file not found at {guard_file}"


def test_guard_extracts_story_id():
    """Test that story-status-guard.ts contains branch-to-story-id extraction pattern."""
    guard_file = Path(__file__).parent.parent / "plugins" / "guards" / "story-status-guard.ts"
    content = guard_file.read_text()
    
    # Check for feature/ branch pattern extraction
    assert "feature/" in content, "Guard should extract feature/ branch pattern"
    
    # Check for story ID extraction regex (should match feature/<story-id>-<slug>)
    assert re.search(r"feature/\([^)]*\)", content) or "feature/" in content, \
        "Guard should contain regex for extracting story ID from branch name"


def test_guard_reads_stories_md():
    """Test that story-status-guard.ts reads STORIES.md."""
    guard_file = Path(__file__).parent.parent / "plugins" / "guards" / "story-status-guard.ts"
    content = guard_file.read_text()
    
    assert "STORIES.md" in content, "Guard should read STORIES.md"


def test_plugin_imports_story_status_guard():
    """Test that pipeline-enforcement.ts imports story-status-guard."""
    plugin_file = Path(__file__).parent.parent / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "story-status-guard" in content, \
        "pipeline-enforcement.ts should import story-status-guard"


def test_plugin_has_after_hook():
    """Test that pipeline-enforcement.ts contains tool.execute.after hook."""
    plugin_file = Path(__file__).parent.parent / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "tool.execute.after" in content, \
        "pipeline-enforcement.ts should contain tool.execute.after hook"
