"""Pipeline status aggregation script tests.

Tests for scripts/pipeline_status.py — deterministic JSON output of pipeline state.
Uses repo's own files as fixtures (FEATURES.md, docs/features/*/feature.md, .pipeline/).
No external systems, no fakes needed — repo files are the test data.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "pipeline_status.py"


def test_script_exists() -> None:
    """Script exists and compiles (syntax check)."""
    assert SCRIPT.exists(), f"Script not found: {SCRIPT}"
    
    # Verify it compiles (syntax check)
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(SCRIPT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script syntax error:\n{result.stderr}"


def test_output_is_valid_json() -> None:
    """Full status output is parseable JSON."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    
    # Parse JSON
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Output is not valid JSON:\n{result.stdout}\nError: {e}") from e
    
    # Basic structure check
    assert isinstance(data, dict), "Output must be a JSON object"
    assert "features" in data, "Output must contain 'features' key"


def test_features_included() -> None:
    """Output contains features list with status."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    
    data = json.loads(result.stdout)
    
    # Check features structure
    assert "features" in data
    features = data["features"]
    assert isinstance(features, list), "features must be a list"
    
    # If features exist, check structure
    if features:
        for feature in features:
            assert "id" in feature, "Each feature must have 'id'"
            assert "title" in feature, "Each feature must have 'title'"
            assert "status" in feature, "Each feature must have 'status'"
            assert feature["status"] in ("done", "in-progress", "planned", "unknown"), \
                f"Invalid status: {feature['status']}"


def test_empty_repo_no_crash() -> None:
    """Script handles repo with no features/stories gracefully."""
    # Create a temporary empty repo structure
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create minimal structure
        (tmppath / ".pipeline").mkdir()
        (tmppath / ".pipeline" / "intent.json").write_text('{"intents": []}')
        (tmppath / ".pipeline" / "qa-state").mkdir()
        (tmppath / "FEATURES.md").write_text("# FEATURES\n\n| Feature | Title | Status |\n|---------|-------|--------|")
        (tmppath / "docs" / "features").mkdir(parents=True)
        
        # Run script in empty repo
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=str(tmppath),
            capture_output=True,
            text=True,
        )
        
        # Should not crash
        assert result.returncode == 0, f"Script crashed on empty repo:\n{result.stderr}"
        
        # Output should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Invalid JSON on empty repo:\n{result.stdout}") from e


def test_story_filter() -> None:
    """--story flag filters to single story."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--story", "06-05"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed with --story flag:\n{result.stderr}"
    
    data = json.loads(result.stdout)
    
    # Should have stories key
    assert "stories" in data, "Filtered output must contain 'stories' key"
    
    # If stories exist, they should match the filter
    stories = data.get("stories", [])
    if stories:
        for story in stories:
            assert "id" in story, "Each story must have 'id'"
            # Story ID should contain the filter
            assert "06-05" in story.get("id", ""), \
                f"Story {story.get('id')} does not match filter '06-05'"
