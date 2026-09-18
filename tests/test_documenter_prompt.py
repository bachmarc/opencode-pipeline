"""
Tests for Story 08-03: Documenter prompt enhancements.

Verifies that agent/documenter.md contains:
1. Instructions to generate docs/requirements.md as derived summary
2. Instructions to generate docs/design.md as derived summary
3. Consistency check instructions
4. Explanation that summaries serve as Architect quick-start
5. Clarification that summaries are derived (not primary sources)
6. Preservation of existing reconciliation duties
7. Boundary section with "do not invent" clarification
8. Valid YAML frontmatter without model: key
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

    def test_instructs_generate_requirements_summary(self):
        """Asserts documenter.md contains instruction to generate/update docs/requirements.md as derived summary."""
        content = read_documenter_md()
        # Should mention generating/updating docs/requirements.md
        assert "docs/requirements.md" in content, "Missing instruction for docs/requirements.md"
        # Should indicate it's a feature overview or derived summary
        assert (
            "feature overview" in content.lower()
            or "derived" in content.lower()
        ), "Missing indication that requirements.md is a feature overview or derived summary"

    def test_instructs_generate_design_summary(self):
        """Asserts documenter.md contains instruction to generate/update docs/design.md as derived summary."""
        content = read_documenter_md()
        # Should mention generating/updating docs/design.md
        assert "docs/design.md" in content, "Missing instruction for docs/design.md"
        # Should indicate it's an architecture summary or derived
        assert (
            "architecture summary" in content.lower()
            or "derived" in content.lower()
        ), "Missing indication that design.md is an architecture summary or derived"

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

    def test_summaries_as_architect_quickstart(self):
        """Asserts documenter.md mentions summaries serving as Architect quick-start (or equivalent phrasing)."""
        content = read_documenter_md()
        # Should mention architect quick-start or similar
        assert (
            "quick-start" in content.lower()
            or "quick start" in content.lower()
            or "architect" in content.lower()
        ), "Missing reference to Architect quick-start"

    def test_summaries_are_derived(self):
        """Asserts documenter.md contains 'derived' or equivalent language clarifying summaries are not primary sources."""
        content = read_documenter_md()
        # Should explicitly state summaries are derived
        assert "derived" in content.lower(), "Missing 'derived' language"
        # Should clarify they are not primary sources
        assert (
            "not a primary" in content.lower()
            or "not primary" in content.lower()
            or "derived from" in content.lower()
        ), "Missing clarification that summaries are not primary sources"

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
