"""
Tests for documentation model migration.

Tests verify that all feature.md and story files have been migrated from the old format
(REQ-IDs, Traceability, Scope, Definition, Development goal) to the new format
(Vision, Context, Feature reference, Context/Purpose, Requirements).
"""

import re
from pathlib import Path
import yaml


def get_all_feature_files():
    """Get all feature.md files under docs/features/*/feature.md."""
    features_dir = Path(__file__).parent.parent / "docs" / "features"
    feature_files = list(features_dir.glob("*/feature.md"))
    return sorted(feature_files)


def get_all_story_files():
    """Get all story files under docs/features/*/stories/*.md, excluding templates."""
    docs_path = Path(__file__).parent.parent / "docs" / "features"
    story_files = []

    for feature_dir in docs_path.glob("*/stories"):
        for story_file in feature_dir.glob("*.md"):
            # Exclude template files
            if story_file.name.startswith("_"):
                continue
            story_files.append(story_file)

    return sorted(story_files)


def read_frontmatter(file_path):
    """Extract YAML frontmatter from a markdown file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match frontmatter between --- markers
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def read_file_content(file_path):
    """Read the full content of a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


# === Feature.md migration tests (Story 09-01) ===


def test_all_features_have_vision_context():
    """All feature.md files must have ## Vision and ## Context sections."""
    feature_files = get_all_feature_files()
    assert len(feature_files) > 0, "No feature.md files found"

    for feature_file in feature_files:
        content = read_file_content(feature_file)

        has_vision = "## Vision" in content
        has_context = "## Context" in content

        assert has_vision, f"{feature_file.name}: Missing '## Vision' section"
        assert has_context, f"{feature_file.name}: Missing '## Context' section"


def test_no_features_have_scope():
    """No feature.md file should have ## Scope section."""
    feature_files = get_all_feature_files()
    assert len(feature_files) > 0, "No feature.md files found"

    for feature_file in feature_files:
        content = read_file_content(feature_file)

        has_scope = "## Scope" in content
        assert not has_scope, f"{feature_file.name}: Should not have '## Scope' section"


def test_no_features_have_req_ids():
    """No feature.md frontmatter should have non-empty req: with REQ- values."""
    feature_files = get_all_feature_files()
    assert len(feature_files) > 0, "No feature.md files found"

    for feature_file in feature_files:
        frontmatter = read_frontmatter(feature_file)

        if frontmatter is None:
            continue

        req_field = frontmatter.get("req")

        # req: [] is OK (empty list)
        # req: missing is OK
        # req: [REQ-xxx] is NOT OK
        if req_field is not None and isinstance(req_field, list):
            for item in req_field:
                assert not str(item).startswith("REQ-"), \
                    f"{feature_file.name}: req field contains REQ-ID: {item}"


# === Story file migration tests (Story 09-02) ===


def test_all_stories_have_feature_reference():
    """All story files must have a 'Feature:' line (not 'Traceability:')."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)
        assert re.search(r"^Feature:\s+", content, re.MULTILINE), \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Missing 'Feature:' line"


def test_no_stories_have_traceability():
    """No story file should have a 'Traceability:' line."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)
        assert not re.search(r"^Traceability:\s+", content, re.MULTILINE), \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Still has 'Traceability:' line"


def test_all_stories_have_context_section():
    """All story files must have '## Context / Purpose' section."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)
        assert re.search(r"^##\s+Context\s*/\s*Purpose", content, re.MULTILINE), \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Missing '## Context / Purpose' section"


def test_all_stories_have_requirements_section():
    """All story files must have '## Requirements' section."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)
        assert re.search(r"^##\s+Requirements", content, re.MULTILINE), \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Missing '## Requirements' section"


def test_no_stories_have_old_sections():
    """No story file should have '## Definition' or '## Development goal' sections."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)

        # Check for old section headers (case-insensitive for German variants)
        has_definition = re.search(r"^##\s+Definition", content, re.MULTILINE | re.IGNORECASE)
        has_dev_goal = re.search(r"^##\s+(Development goal|Entwicklungsziel)", content, re.MULTILINE | re.IGNORECASE)

        assert not has_definition, \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Still has '## Definition' section"
        assert not has_dev_goal, \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Still has old development goal section"
