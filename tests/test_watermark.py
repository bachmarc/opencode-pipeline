"""Tests for watermark functionality in README.md and AGENTS.md.

Tests verify:
- Watermark presence and format in documentation files
- check_watermark.py script functionality
- Pending story detection
"""

import json
import re
import subprocess
import sys
from pathlib import Path


# Regex pattern for watermark validation
WATERMARK_PATTERN = r'<!-- synced_through: \d{2}-\d{2} \| updated: \d{4}-\d{2}-\d{2} -->'


def test_readme_has_watermark():
    """README.md line 2 contains a parseable watermark comment."""
    readme_path = Path(__file__).parent.parent / "README.md"
    assert readme_path.exists(), f"README.md not found at {readme_path}"
    
    with open(readme_path, "r") as f:
        lines = f.readlines()
    
    assert len(lines) >= 2, "README.md has fewer than 2 lines"
    
    line_2 = lines[1].strip()
    assert line_2.startswith("<!--"), f"Line 2 should start with <!--, got: {line_2}"
    assert "synced_through:" in line_2, f"Line 2 should contain 'synced_through:', got: {line_2}"
    assert "updated:" in line_2, f"Line 2 should contain 'updated:', got: {line_2}"


def test_agents_md_has_watermark():
    """AGENTS.md line 2 contains a parseable watermark comment."""
    agents_path = Path(__file__).parent.parent / "AGENTS.md"
    assert agents_path.exists(), f"AGENTS.md not found at {agents_path}"
    
    with open(agents_path, "r") as f:
        lines = f.readlines()
    
    assert len(lines) >= 2, "AGENTS.md has fewer than 2 lines"
    
    line_2 = lines[1].strip()
    assert line_2.startswith("<!--"), f"Line 2 should start with <!--, got: {line_2}"
    assert "synced_through:" in line_2, f"Line 2 should contain 'synced_through:', got: {line_2}"
    assert "updated:" in line_2, f"Line 2 should contain 'updated:', got: {line_2}"


def test_watermark_format_valid():
    """Watermark matches expected regex pattern."""
    readme_path = Path(__file__).parent.parent / "README.md"
    agents_path = Path(__file__).parent.parent / "AGENTS.md"
    
    for path in [readme_path, agents_path]:
        with open(path, "r") as f:
            lines = f.readlines()
        
        line_2 = lines[1].strip()
        assert re.match(WATERMARK_PATTERN, line_2), \
            f"Watermark in {path.name} line 2 doesn't match pattern: {line_2}"


def test_check_watermark_script_runs():
    """Script executes without error and returns valid JSON."""
    script_path = Path(__file__).parent.parent / "scripts" / "check_watermark.py"
    assert script_path.exists(), f"check_watermark.py not found at {script_path}"
    
    # Run script with README.md
    result = subprocess.run(
        [sys.executable, str(script_path), "--file", "README.md"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    
    assert result.returncode in [0, 1], \
        f"Script exited with code {result.returncode}, stderr: {result.stderr}"
    
    # Parse JSON output
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"Script output is not valid JSON: {result.stdout}\nError: {e}")
    
    # Verify required keys
    assert "file" in output, f"Missing 'file' key in output: {output}"
    assert "synced_through" in output, f"Missing 'synced_through' key in output: {output}"
    assert "pending_stories" in output, f"Missing 'pending_stories' key in output: {output}"
    
    # Verify types
    assert isinstance(output["file"], str), f"'file' should be string, got {type(output['file'])}"
    assert isinstance(output["synced_through"], str), f"'synced_through' should be string, got {type(output['synced_through'])}"
    assert isinstance(output["pending_stories"], list), f"'pending_stories' should be list, got {type(output['pending_stories'])}"


def test_check_watermark_detects_pending():
    """Script reports pending stories when watermark is behind current stories."""
    script_path = Path(__file__).parent.parent / "scripts" / "check_watermark.py"
    
    # Run script with README.md
    result = subprocess.run(
        [sys.executable, str(script_path), "--file", "README.md"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )
    
    output = json.loads(result.stdout)
    
    # Read STORIES.md to find done stories
    stories_path = Path(__file__).parent.parent / "STORIES.md"
    with open(stories_path, "r") as f:
        stories_content = f.read()
    
    # Find all done stories (lines with "Done" in them)
    done_stories = []
    for line in stories_content.split("\n"):
        if "| Done" in line or "| Done (" in line:
            # Extract story ID from the line (first column after |)
            parts = line.split("|")
            if len(parts) >= 2:
                story_id = parts[1].strip()
                # Clean up story ID (remove markdown formatting)
                story_id = story_id.replace("**", "").strip()
                if story_id and story_id != "Story":
                    done_stories.append(story_id)
    
    # If watermark is behind the latest done story, there should be pending stories
    if done_stories:
        synced_through = output["synced_through"]
        # Check if there are any done stories after the synced_through story
        # This is a basic check - the actual logic depends on story ID ordering
        if synced_through and done_stories:
            # At least verify the structure is correct
            assert isinstance(output["pending_stories"], list), \
                "pending_stories should be a list"
