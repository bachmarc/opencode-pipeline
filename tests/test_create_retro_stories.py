"""Tests for retro story generator script (Story 12-05).

Tests for create_retro_stories.py which creates retro feature and story files
from a JSON definition. Uses temporary directories for all tests.
Retro feature folder uses F-RETRO-retro naming convention.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from create_retro_stories import create_retro_stories


@pytest.fixture
def retro_def_single() -> dict:
    """Single retro story definition."""
    return {
        "feature_id": "F-RETRO",
        "feature_title": "Pre-Pipeline Development",
        "stories": [
            {
                "id": "RETRO-01",
                "slug": "initial-development",
                "title": "Initial Development",
                "summary": "All development before pipeline adoption."
            }
        ]
    }


@pytest.fixture
def retro_def_multiple() -> dict:
    """Multiple retro stories definition."""
    return {
        "feature_id": "F-RETRO",
        "feature_title": "Pre-Pipeline Development",
        "stories": [
            {
                "id": "RETRO-01",
                "slug": "initial-development",
                "title": "Initial Development",
                "summary": "Initial setup and core functionality."
            },
            {
                "id": "RETRO-02",
                "slug": "feature-expansion",
                "title": "Feature Expansion",
                "summary": "Added additional features and integrations."
            },
            {
                "id": "RETRO-03",
                "slug": "stabilization",
                "title": "Stabilization",
                "summary": "Bug fixes and performance improvements."
            }
        ]
    }


def test_creates_retro_feature_dir(tmp_path: Path, retro_def_single: dict) -> None:
    """Temp dir → docs/features/F-RETRO-retro/ created."""
    result = create_retro_stories(str(tmp_path), retro_def_single)
    
    retro_dir = tmp_path / "docs" / "features" / "F-RETRO-retro"
    assert retro_dir.is_dir(), f"Retro feature directory not created: {retro_dir}"
    assert result["created"], "Should have created files"


def test_creates_feature_md(tmp_path: Path, retro_def_single: dict) -> None:
    """Temp dir → docs/features/F-RETRO-retro/feature.md exists with F-RETRO id."""
    result = create_retro_stories(str(tmp_path), retro_def_single)
    
    feature_md = tmp_path / "docs" / "features" / "F-RETRO-retro" / "feature.md"
    assert feature_md.is_file(), f"Feature file not created: {feature_md}"
    
    content = feature_md.read_text(encoding="utf-8")
    assert "F-RETRO" in content, "Feature file should contain F-RETRO id"
    assert "id: F-RETRO" in content, "Feature file should have id field"
    assert "Pre-Pipeline Development" in content, "Feature file should contain feature title"


def test_creates_single_retro_story(tmp_path: Path, retro_def_single: dict) -> None:
    """Input with 1 story → one story file created with Retro-Done status."""
    result = create_retro_stories(str(tmp_path), retro_def_single)
    
    story_file = tmp_path / "docs" / "features" / "F-RETRO-retro" / "stories" / "RETRO-01-initial-development.md"
    assert story_file.is_file(), f"Story file not created: {story_file}"
    
    content = story_file.read_text(encoding="utf-8")
    assert "Retro-Done" in content, "Story should have Retro-Done status"
    assert "RETRO-01" in content, "Story should contain story ID"
    assert "Initial Development" in content, "Story should contain story title"
    
    # Should have created feature.md, story file, FEATURES.md, and STORIES.md
    assert len(result["created"]) >= 3, "Should have created at least 3 files"


def test_creates_multiple_retro_stories(tmp_path: Path, retro_def_multiple: dict) -> None:
    """Input with 3 stories → three story files created."""
    result = create_retro_stories(str(tmp_path), retro_def_multiple)
    
    stories_dir = tmp_path / "docs" / "features" / "F-RETRO-retro" / "stories"
    assert stories_dir.is_dir(), "Stories directory should be created"
    
    story_files = list(stories_dir.glob("RETRO-*.md"))
    assert len(story_files) == 3, f"Should have created 3 story files, got {len(story_files)}"
    
    # Check each story file exists and has correct status
    for i, story_def in enumerate(retro_def_multiple["stories"], 1):
        story_file = stories_dir / f"{story_def['id']}-{story_def['slug']}.md"
        assert story_file.is_file(), f"Story file not created: {story_file}"
        
        content = story_file.read_text(encoding="utf-8")
        assert "Retro-Done" in content, f"Story {i} should have Retro-Done status"


def test_updates_features_md(tmp_path: Path, retro_def_single: dict) -> None:
    """Temp dir with existing FEATURES.md → F-RETRO entry appended."""
    # Create existing FEATURES.md with table header
    features_md = tmp_path / "FEATURES.md"
    features_md.write_text(
        "# FEATURES\n\n"
        "| Feature | Title | Status | Owner | Stories |\n"
        "|---------|-------|--------|-------|----------|\n"
        "| F-001 | Foundation | done | — | 01-03, 01-04 |\n",
        encoding="utf-8"
    )
    
    result = create_retro_stories(str(tmp_path), retro_def_single)
    
    content = features_md.read_text(encoding="utf-8")
    assert "F-RETRO" in content, "FEATURES.md should contain F-RETRO entry"
    assert "Pre-Pipeline Development" in content, "FEATURES.md should contain feature title"
    assert "updated" in result, "Should report updated files"


def test_updates_stories_md(tmp_path: Path, retro_def_multiple: dict) -> None:
    """Temp dir with existing STORIES.md → retro entries appended."""
    # Create existing STORIES.md with table header
    stories_md = tmp_path / "STORIES.md"
    stories_md.write_text(
        "# STORIES\n\n"
        "| Story | Title | Status |\n"
        "|-------|-------|--------|\n"
        "| 01-03 | Test | Done |\n",
        encoding="utf-8"
    )
    
    result = create_retro_stories(str(tmp_path), retro_def_multiple)
    
    content = stories_md.read_text(encoding="utf-8")
    assert "RETRO-01" in content, "STORIES.md should contain RETRO-01"
    assert "RETRO-02" in content, "STORIES.md should contain RETRO-02"
    assert "RETRO-03" in content, "STORIES.md should contain RETRO-03"
    assert "Retro-Done" in content, "STORIES.md should contain Retro-Done status"


def test_creates_indexes_if_missing(tmp_path: Path, retro_def_single: dict) -> None:
    """Temp dir without FEATURES.md → FEATURES.md created with retro entry."""
    result = create_retro_stories(str(tmp_path), retro_def_single)
    
    features_md = tmp_path / "FEATURES.md"
    assert features_md.is_file(), "FEATURES.md should be created if missing"
    
    content = features_md.read_text(encoding="utf-8")
    assert "F-RETRO" in content, "Created FEATURES.md should contain F-RETRO"
    assert "| Feature" in content, "Created FEATURES.md should have table header"
    
    stories_md = tmp_path / "STORIES.md"
    assert stories_md.is_file(), "STORIES.md should be created if missing"
    
    content = stories_md.read_text(encoding="utf-8")
    assert "RETRO-01" in content, "Created STORIES.md should contain RETRO-01"


def test_never_overwrites_existing_retro(tmp_path: Path, retro_def_single: dict) -> None:
    """Temp dir with existing retro story → not overwritten, in skipped list."""
    # Create existing retro story
    stories_dir = tmp_path / "docs" / "features" / "F-RETRO-retro" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    
    story_file = stories_dir / "RETRO-01-initial-development.md"
    original_content = "# Original content\n\nThis should not be overwritten."
    story_file.write_text(original_content, encoding="utf-8")
    
    result = create_retro_stories(str(tmp_path), retro_def_single)
    
    # Check file was not overwritten
    content = story_file.read_text(encoding="utf-8")
    assert content == original_content, "Existing story file should not be overwritten"
    
    # Check it's in skipped list
    assert "skipped" in result, "Result should have skipped list"
    assert any("RETRO-01" in str(f) for f in result["skipped"]), "Skipped file should be in result"
