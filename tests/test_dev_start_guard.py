"""Tests for dev-start guard — warns when developer/qa-manager spawned without story."""

import re
from pathlib import Path


def test_dev_start_guard_file_exists():
    """plugins/guards/dev-start-guard.ts exists."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    assert guard_file.exists(), f"Guard file not found at {guard_file}"


def test_dev_start_guard_has_story_regex():
    """plugins/guards/dev-start-guard.ts contains story ID regex pattern."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    content = guard_file.read_text()

    # Check for the story ID regex pattern \d{2}-\d{2}
    assert r"\d{2}-\d{2}" in content or "\\d{2}-\\d{2}" in content, \
        "Story ID regex pattern (\\d{2}-\\d{2}) not found in guard file"


def test_dev_start_guard_uses_story_files_not_stories_md():
    """plugins/guards/dev-start-guard.ts scans story files, not STORIES.md (story 37-03).
    
    After story 37-03, dev-start-guard.ts validates story IDs by scanning
    docs/features/*/stories/*.md filenames, not reading STORIES.md.
    """
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    content = guard_file.read_text()

    # Assert STORIES.md is NOT referenced in the guard
    assert "STORIES.md" not in content, (
        "dev-start-guard.ts should NOT reference STORIES.md "
        "(story 37-03 replaces STORIES.md scan with story-file scan)"
    )
    
    # Assert it DOES reference story files pattern
    assert "docs/features" in content or "stories" in content, (
        "dev-start-guard.ts should scan docs/features/*/stories/*.md for story IDs"
    )


def test_plugin_imports_dev_start_guard():
    """plugins/pipeline-enforcement.ts imports dev-start-guard."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()

    assert "dev-start-guard" in content, "dev-start-guard import not found in pipeline-enforcement.ts"


def test_explicit_marker_pattern_in_guard():
    """Guard file contains [story: pattern for explicit marker parsing.
    
    The guard should look for explicit [story: XX-YY] markers in prompts
    to avoid false positives from other XX-YY patterns in the text.
    """
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    content = guard_file.read_text()

    # Check for explicit marker pattern (case-insensitive, allows whitespace)
    assert "[story:" in content or "[story :" in content, \
        "Explicit [story: marker pattern not found in guard file"


def test_guard_has_fallback_warning():
    """Guard file contains fallback warning text.
    
    When no explicit marker is found, the guard should warn about using
    fallback pattern matching.
    """
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    content = guard_file.read_text()

    assert "fallback" in content.lower(), \
        "Fallback warning text not found in guard file"


def test_guard_has_parse_explicit_function():
    """Guard file contains parseExplicitStoryId function.
    
    The guard should have a dedicated function to parse explicit [story: XX-YY]
    markers from prompts.
    """
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    content = guard_file.read_text()

    assert "parseExplicitStoryId" in content, \
        "parseExplicitStoryId function not found in guard file"