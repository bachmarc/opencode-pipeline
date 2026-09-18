"""Tests for story and feature templates."""

import re
from pathlib import Path


def test_story_template_has_five_sections():
    """Test that story template has all 5 required sections."""
    template_path = Path("docs/features/_story_template.md")
    assert template_path.exists(), f"{template_path} does not exist"
    
    content = template_path.read_text()
    
    # Check for all 5 required section headings
    required_sections = [
        "## Context / Purpose",
        "## Requirements",
        "## Developer Targets",
        "## Acceptance criteria",
        "## Test criteria",
    ]
    
    for section in required_sections:
        assert section in content, f"Missing section: {section}"


def test_story_template_no_req_ids():
    """Test that story template does not contain REQ- or Design § references."""
    template_path = Path("docs/features/_story_template.md")
    content = template_path.read_text()
    
    # Check for REQ- pattern
    assert not re.search(r"REQ-\d+", content), "Story template contains REQ-IDs"
    
    # Check for Design § pattern
    assert "Design §" not in content, "Story template contains Design § references"


def test_story_template_has_feature_reference():
    """Test that story template contains Feature: line instead of Traceability."""
    template_path = Path("docs/features/_story_template.md")
    content = template_path.read_text()
    
    # Check for Feature: line
    assert "Feature:" in content, "Story template missing 'Feature:' line"
    
    # Check that old Traceability line is gone
    assert "Traceability:" not in content, "Story template still contains old 'Traceability:' line"


def test_feature_template_has_vision_context():
    """Test that feature template has Vision and Context sections."""
    template_path = Path("docs/features/_feature_template.md")
    assert template_path.exists(), f"{template_path} does not exist"
    
    content = template_path.read_text()
    
    assert "## Vision" in content, "Feature template missing '## Vision' section"
    assert "## Context" in content, "Feature template missing '## Context' section"


def test_feature_template_has_frontmatter():
    """Test that feature template has YAML frontmatter with required fields."""
    template_path = Path("docs/features/_feature_template.md")
    content = template_path.read_text()
    
    # Check for YAML frontmatter
    assert content.startswith("---"), "Feature template missing YAML frontmatter start"
    
    # Extract frontmatter
    parts = content.split("---", 2)
    assert len(parts) >= 3, "Feature template frontmatter not properly closed"
    
    frontmatter = parts[1]
    
    # Check for required fields
    required_fields = ["id:", "title:", "status:", "owner:"]
    for field in required_fields:
        assert field in frontmatter, f"Feature template frontmatter missing '{field}'"
