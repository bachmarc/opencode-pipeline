"""Tests for Story Status Guard plugin — story 37-03 deletes this guard.

Tests assert that:
1. story-status-guard.ts does NOT exist (deleted)
2. pipeline-enforcement.ts does NOT reference story-status-guard (import removed)
"""

from pathlib import Path


def test_story_status_guard_file_removed():
    """Test that plugins/guards/story-status-guard.ts has been deleted."""
    guard_file = Path(__file__).parent.parent / "plugins" / "guards" / "story-status-guard.ts"
    assert not guard_file.exists(), (
        f"Guard file should be deleted (story 37-03) but found at {guard_file}"
    )


def test_plugin_does_not_import_story_status_guard():
    """Test that pipeline-enforcement.ts no longer imports story-status-guard."""
    plugin_file = Path(__file__).parent.parent / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "story-status-guard" not in content, (
        "pipeline-enforcement.ts should not reference story-status-guard "
        "(guard deleted in story 37-03)"
    )
