"""
Tests for Story 14-01: Remove Derived Docs (requirements.md + design.md).

Verifies that:
1. docs/requirements.md does not exist
2. docs/design.md does not exist
3. No agent prompts instruct creating/maintaining these files
4. No commands reference these files for generation
5. No scripts create these files
"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_requirements_md_does_not_exist() -> None:
    """docs/requirements.md should not exist."""
    requirements_path = REPO_ROOT / "docs" / "requirements.md"
    assert not requirements_path.exists(), (
        f"docs/requirements.md should not exist (derived docs removed in 14-01)"
    )


def test_design_md_does_not_exist() -> None:
    """docs/design.md should not exist."""
    design_path = REPO_ROOT / "docs" / "design.md"
    assert not design_path.exists(), (
        f"docs/design.md should not exist (derived docs removed in 14-01)"
    )


def test_architect_instructs_read_features_md() -> None:
    """agent/architect.md should instruct reading FEATURES.md (not requirements.md)."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    # Should mention FEATURES.md
    assert "FEATURES.md" in content, (
        "architect.md: should instruct reading FEATURES.md for quick overview"
    )


def test_architect_no_derived_doc_references() -> None:
    """agent/architect.md should not instruct creating/maintaining requirements.md or design.md."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    # Should NOT mention generating requirements.md or design.md
    forbidden_patterns = [
        "generate requirements.md",
        "generate design.md",
        "maintain requirements.md",
        "maintain design.md",
        "create requirements.md",
        "create design.md",
    ]

    for pattern in forbidden_patterns:
        assert pattern.lower() not in content.lower(), (
            f"architect.md: contains forbidden pattern {pattern!r} "
            f"(derived docs should not be generated)"
        )


def test_documenter_no_requirements_generation() -> None:
    """agent/documenter.md should not instruct generating requirements.md."""
    documenter_path = REPO_ROOT / "agent" / "documenter.md"
    assert documenter_path.is_file(), f"missing {documenter_path.relative_to(REPO_ROOT)}"

    content = documenter_path.read_text(encoding="utf-8")

    # Should NOT mention generating requirements.md
    forbidden_patterns = [
        "generate requirements.md",
        "generate docs/requirements.md",
        "create requirements.md",
        "create docs/requirements.md",
    ]

    for pattern in forbidden_patterns:
        assert pattern.lower() not in content.lower(), (
            f"documenter.md: contains forbidden pattern {pattern!r} "
            f"(requirements.md should not be generated)"
        )


def test_documenter_no_design_generation() -> None:
    """agent/documenter.md should not instruct generating design.md."""
    documenter_path = REPO_ROOT / "agent" / "documenter.md"
    assert documenter_path.is_file(), f"missing {documenter_path.relative_to(REPO_ROOT)}"

    content = documenter_path.read_text(encoding="utf-8")

    # Should NOT mention generating design.md
    forbidden_patterns = [
        "generate design.md",
        "generate docs/design.md",
        "create design.md",
        "create docs/design.md",
    ]

    for pattern in forbidden_patterns:
        assert pattern.lower() not in content.lower(), (
            f"documenter.md: contains forbidden pattern {pattern!r} "
            f"(design.md should not be generated)"
        )
