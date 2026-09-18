"""Tests for feature.md migration to new format (Vision + Context)."""

import re
from pathlib import Path
import yaml


def get_all_feature_files():
    """Get all feature.md files under docs/features/*/feature.md."""
    features_dir = Path(__file__).parent.parent / "docs" / "features"
    feature_files = list(features_dir.glob("*/feature.md"))
    return sorted(feature_files)


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
