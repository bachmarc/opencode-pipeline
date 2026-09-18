"""Tests for dev-start guard — warns when developer/qa-manager spawned without story."""

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


def test_dev_start_guard_reads_stories():
    """plugins/guards/dev-start-guard.ts contains reference to STORIES.md."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    content = guard_file.read_text()
    
    assert "STORIES.md" in content, "STORIES.md reference not found in guard file"


def test_plugin_imports_dev_start_guard():
    """plugins/pipeline-enforcement.ts imports dev-start-guard."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "dev-start-guard" in content, "dev-start-guard import not found in pipeline-enforcement.ts"
