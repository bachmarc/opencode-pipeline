"""Feature hierarchy file structure tests.

Tests for the new docs/features/ directory layout with feature.md and stories/ subdirs.
Validates that FEATURES.md exists, feature directories are properly structured,
and story files are migrated from docs/stories/ to docs/features/<name>/stories/.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_features_md_exists() -> None:
    """FEATURES.md exists at repo root."""
    features_md = REPO_ROOT / "FEATURES.md"
    assert features_md.is_file(), f"FEATURES.md not found at {features_md}"


def test_features_md_has_table() -> None:
    """FEATURES.md contains Markdown table with required columns."""
    features_md = REPO_ROOT / "FEATURES.md"
    content = features_md.read_text(encoding="utf-8")
    
    # Check for table header with required columns
    required_columns = ("Feature", "Title", "Status", "Owner", "Stories", "Traceability")
    for col in required_columns:
        assert col in content, f"FEATURES.md missing column: {col}"
    
    # Check for at least one table row (pipe-delimited)
    lines = content.splitlines()
    table_rows = [line for line in lines if line.strip().startswith("|")]
    assert len(table_rows) >= 3, "FEATURES.md must have header, separator, and at least one data row"


def test_feature_dirs_exist() -> None:
    """Every feature listed in FEATURES.md has a corresponding docs/features/<name>/ directory."""
    features_md = REPO_ROOT / "FEATURES.md"
    content = features_md.read_text(encoding="utf-8")
    
    # Extract feature IDs from table (first column after |)
    # Skip header and separator rows
    lines = content.splitlines()
    feature_ids = []
    in_table = False
    for i, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        # Skip header row (contains "Feature" as column name)
        if "Feature" in line and "Title" in line:
            in_table = True
            continue
        # Skip separator row (contains dashes)
        if "---" in line:
            continue
        if not in_table:
            continue
        # Parse table row: | Feature | Title | ...
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > 1 and parts[1] and parts[1] not in ("Feature", ""):
            feature_ids.append(parts[1])
    
    assert feature_ids, "No features found in FEATURES.md table"
    
    features_dir = REPO_ROOT / "docs" / "features"
    assert features_dir.is_dir(), f"docs/features/ directory not found"
    
    # Map feature IDs to directory names
    # F-RETRO -> retro, F-001 -> foundation, F-002 -> i18n, F-003 -> docs, F-004 -> pipeline-evolution
    id_to_dir = {
        "F-RETRO": "retro",
        "F-001": "foundation",
        "F-002": "i18n",
        "F-003": "docs",
        "F-004": "pipeline-evolution",
        "F-005": "doc-model-reform",
        "F-006": "doc-model-migration",
    }
    
    for feature_id in feature_ids:
        dir_name = id_to_dir.get(feature_id, feature_id.lower())
        feature_path = features_dir / dir_name
        assert feature_path.is_dir(), f"Feature directory not found: {feature_path}"


def test_feature_md_fields() -> None:
    """Each feature.md contains required fields (id, title, status, req)."""
    features_dir = REPO_ROOT / "docs" / "features"
    
    if not features_dir.is_dir():
        return  # Skip if features dir doesn't exist yet
    
    feature_mds = list(features_dir.glob("*/feature.md"))
    assert feature_mds, "No feature.md files found in docs/features/"
    
    required_fields = ("id", "title", "status", "req")
    
    for feature_md in feature_mds:
        content = feature_md.read_text(encoding="utf-8")
        
        # Check for YAML-like header with required fields
        for field in required_fields:
            # Look for field: value pattern (case-insensitive)
            pattern = rf"^{field}:\s*"
            assert re.search(pattern, content, re.MULTILINE | re.IGNORECASE), (
                f"{feature_md.relative_to(REPO_ROOT)}: missing field '{field}'"
            )


def test_story_files_in_features() -> None:
    """Story files exist under docs/features/<name>/stories/, not under docs/stories/."""
    features_dir = REPO_ROOT / "docs" / "features"
    stories_dir = REPO_ROOT / "docs" / "stories"
    
    if not features_dir.is_dir():
        return  # Skip if features dir doesn't exist yet
    
    # Check that story files exist in features subdirs
    feature_story_files = list(features_dir.glob("*/stories/*.md"))
    assert feature_story_files, "No story files found in docs/features/*/stories/"
    
    # Check that old docs/stories/ directory does not exist
    assert not stories_dir.exists(), (
        f"Legacy docs/stories/ directory should not exist"
    )


def test_story_template_exists() -> None:
    """docs/features/_story_template.md exists."""
    template_path = REPO_ROOT / "docs" / "features" / "_story_template.md"
    assert template_path.is_file(), f"Story template not found at {template_path}"


def test_no_legacy_stories_dir() -> None:
    """docs/stories/ directory does not exist (legacy directory removed)."""
    stories_dir = REPO_ROOT / "docs" / "stories"
    assert not stories_dir.exists(), (
        f"Legacy docs/stories/ directory should not exist, but found at {stories_dir}"
    )
