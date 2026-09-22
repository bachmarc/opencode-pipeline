"""
Tests for Story 08-03: Documenter prompt enhancements (updated for 14-01).

Verifies that agent/documenter.md:
1. Does NOT contain instructions to generate docs/requirements.md
2. Does NOT contain instructions to generate docs/design.md
3. Contains consistency check instructions
4. Preserves existing reconciliation duties (README, docstrings, stale comments)
5. Has a Boundary section with "do not invent" clarification
6. Has valid YAML frontmatter without model: key
"""

import re
import yaml
from pathlib import Path


def read_documenter_md():
    """Read the documenter.md file."""
    path = Path(__file__).parent.parent / "agent" / "documenter.md"
    return path.read_text(encoding="utf-8")


def extract_frontmatter(content):
    """Extract YAML frontmatter from markdown file."""
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


class TestDocumenterPrompt:
    """Test suite for documenter.md enhancements."""

    def test_no_requirements_generation(self):
        """Asserts documenter.md does NOT contain instruction to generate docs/requirements.md."""
        content = read_documenter_md()
        # Should NOT mention generating/updating docs/requirements.md
        assert "generate requirements.md" not in content.lower(), "documenter.md should not generate requirements.md"
        assert "generate docs/requirements.md" not in content.lower(), "documenter.md should not generate docs/requirements.md"

    def test_no_design_generation(self):
        """Asserts documenter.md does NOT contain instruction to generate docs/design.md."""
        content = read_documenter_md()
        # Should NOT mention generating/updating docs/design.md
        assert "generate design.md" not in content.lower(), "documenter.md should not generate design.md"
        assert "generate docs/design.md" not in content.lower(), "documenter.md should not generate docs/design.md"

    def test_has_consistency_checks(self):
        """Asserts documenter.md contains consistency check instructions (orphaned references, stale status)."""
        content = read_documenter_md()
        # Should have a consistency checks section
        assert (
            "consistency check" in content.lower()
            or "verify consistency" in content.lower()
        ), "Missing consistency checks section"
        # Should mention orphaned references or stale status
        assert (
            "orphaned" in content.lower()
            or "stale" in content.lower()
        ), "Missing orphaned references or stale status checks"

    def test_existing_duties_preserved(self):
        """Asserts documenter.md still mentions README, docstrings, stale comments reconciliation."""
        content = read_documenter_md()
        # Should still mention README
        assert "README" in content, "Missing README reconciliation duty"
        # Should still mention docstrings
        assert "docstring" in content.lower(), "Missing docstrings reconciliation duty"
        # Should still mention stale comments
        assert "stale comment" in content.lower(), "Missing stale comments reconciliation duty"

    def test_boundary_no_invent(self):
        """Asserts boundary section contains 'do not invent' for requirements/architecture."""
        content = read_documenter_md()
        # Should have a Boundary section
        assert "Boundary" in content, "Missing Boundary section"
        # Should contain "do not invent" or similar
        assert (
            "do not invent" in content.lower()
            or "invent" in content.lower()
        ), "Missing 'do not invent' clarification in Boundary section"

    def test_valid_frontmatter(self):
        """Asserts valid YAML frontmatter without model: key."""
        content = read_documenter_md()
        frontmatter = extract_frontmatter(content)
        
        # Frontmatter must exist and be valid YAML
        assert frontmatter is not None, "Invalid or missing YAML frontmatter"
        
        # Must have description
        assert "description" in frontmatter, "Missing 'description' in frontmatter"
        
        # Must have mode
        assert "mode" in frontmatter, "Missing 'mode' in frontmatter"
        
        # Must NOT have model key
        assert "model" not in frontmatter, "Frontmatter should not contain 'model' key"

    def test_documenter_has_watermark_workflow(self):
        """Asserts agent/documenter.md contains watermark-based workflow keywords."""
        content = read_documenter_md()
        # Should mention watermark
        assert "watermark" in content.lower(), "Missing 'watermark' in documenter.md"
        # Should mention check_watermark script
        assert "check_watermark" in content.lower(), "Missing 'check_watermark' in documenter.md"
        # Should mention synced_through
        assert "synced_through" in content.lower(), "Missing 'synced_through' in documenter.md"

    def test_documenter_has_incremental_steps(self):
        """Asserts the prompt contains incremental workflow steps in the assignment section."""
        content = read_documenter_md()
        # Should mention pending stories
        assert "pending stories" in content.lower(), "Missing 'pending stories' in documenter.md"
        # Should mention bump (for bumping watermark)
        assert "bump" in content.lower(), "Missing 'bump' in documenter.md"

    def test_documenter_has_fallback(self):
        """Asserts the prompt mentions fallback behavior when watermark is missing."""
        content = read_documenter_md()
        # Should mention fallback or missing watermark handling
        assert (
            "fallback" in content.lower()
            or "missing" in content.lower()
        ), "Missing fallback behavior for missing watermark"
