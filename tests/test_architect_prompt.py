"""Tests for architect prompt refactor (Story 08-02, updated for 14-01).

Checks:
1. agent/architect.md does NOT contain instructions to write docs/requirements.md as primary source
2. agent/architect.md does NOT contain instructions to write docs/design.md as primary source
3. agent/architect.md references _feature_template.md
4. agent/architect.md references _story_template.md
5. agent/architect.md instructs reading FEATURES.md (not requirements.md)
6. agent/architect.md preserves architecture guidance (function vs connectivity, fakes, integration tests)
7. "Output after Phase 1+2" section lists feature files and story files (not requirements.md + design.md)
8. agent/architect.md has valid frontmatter without model: key

Stdlib only — no external systems, deterministic (repo files are the fixture).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_frontmatter(text: str, filename: str) -> dict[str, str]:
    """Parse a simple ``---`` delimited key-value frontmatter block.

    Raises AssertionError (with the filename) when the block is missing or
    malformed. Values must be single-line ``key: value`` pairs; the delimiter
    must be exactly ``---``.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError(f"{filename}: frontmatter missing (no leading '---')")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise AssertionError(
            f"{filename}: frontmatter not terminated (no closing '---')"
        ) from None

    meta: dict[str, str] = {}
    for lineno, line in enumerate(lines[1:end], start=2):
        stripped = line.strip()
        if not stripped:  # blank lines inside the block are tolerated
            continue
        if ":" not in stripped:
            raise AssertionError(
                f"{filename}: frontmatter line {lineno} not 'key: value': {stripped!r}"
            )
        key, _, value = stripped.partition(":")
        key = key.strip()
        if not key:
            raise AssertionError(
                f"{filename}: frontmatter line {lineno} has empty key: {stripped!r}"
            )
        meta[key] = value.strip()
    return meta


def test_no_write_requirements_instruction() -> None:
    """agent/architect.md does NOT contain instructions to write docs/requirements.md as primary source."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    # Check for forbidden patterns that indicate writing requirements.md as primary source
    forbidden_patterns = [
        "→ `docs/requirements.md`",
        "write to requirements.md",
        "write requirements.md",
        "Functional / non-functional requirements → `docs/requirements.md`",
    ]

    for pattern in forbidden_patterns:
        assert pattern not in content, (
            f"architect.md: contains forbidden pattern {pattern!r} "
            f"(requirements.md should not be primary source)"
        )


def test_no_write_design_primary() -> None:
    """agent/architect.md does NOT instruct writing design.md as primary source."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    # Check for forbidden patterns that indicate writing design.md as primary source
    # (may mention it as Documenter output, but not as primary instruction)
    forbidden_patterns = [
        "Design architecture` — `docs/design.md` with mandatory sections",
        "Design architecture` — `docs/design.md`",
    ]

    for pattern in forbidden_patterns:
        assert pattern not in content, (
            f"architect.md: contains forbidden pattern {pattern!r} "
            f"(design.md should not be primary source)"
        )


def test_references_feature_template() -> None:
    """agent/architect.md references _feature_template.md."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    assert "_feature_template.md" in content, (
        "architect.md: does not reference _feature_template.md"
    )


def test_references_story_template() -> None:
    """agent/architect.md references _story_template.md."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    assert "_story_template.md" in content, (
        "architect.md: does not reference _story_template.md"
    )


def test_instructs_read_features_md() -> None:
    """agent/architect.md instructs reading FEATURES.md (not requirements.md)."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    # Should contain instruction to read FEATURES.md
    assert "FEATURES.md" in content, (
        "architect.md: does not reference FEATURES.md"
    )

    # Should NOT reference requirements.md as something to read
    assert "docs/requirements.md" not in content, (
        "architect.md: should not reference docs/requirements.md (use FEATURES.md instead)"
    )


def test_architecture_guidance_preserved() -> None:
    """agent/architect.md preserves key architecture guidance phrases."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    # Check for key architecture guidance phrases
    required_phrases = [
        "function vs connectivity",
        "fake",  # for "fake interfaces"
        "integration test",
    ]

    for phrase in required_phrases:
        assert phrase.lower() in content.lower(), (
            f"architect.md: missing key architecture guidance phrase {phrase!r}"
        )


def test_output_phase_lists_features_stories() -> None:
    """'Output after Phase 1+2' section lists feature files and story files."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    # Find the "Output after Phase 1+2" section
    assert "Output after Phase 1+2" in content, (
        "architect.md: missing 'Output after Phase 1+2' section"
    )

    # Extract the section (from "Output after Phase 1+2" to the next "##" or end)
    start_idx = content.find("Output after Phase 1+2")
    next_section_idx = content.find("\n##", start_idx + 1)
    if next_section_idx == -1:
        output_section = content[start_idx:]
    else:
        output_section = content[start_idx:next_section_idx]

    # Check for feature files and story files references
    assert "feature" in output_section.lower(), (
        "architect.md: 'Output after Phase 1+2' section does not mention feature files"
    )
    assert "stor" in output_section.lower(), (
        "architect.md: 'Output after Phase 1+2' section does not mention story files"
    )

    # Should NOT list requirements.md or design.md as primary outputs
    assert "docs/requirements.md" not in output_section or "Documenter" in output_section, (
        "architect.md: 'Output after Phase 1+2' lists requirements.md as primary output"
    )
    assert "docs/design.md" not in output_section or "Documenter" in output_section, (
        "architect.md: 'Output after Phase 1+2' lists design.md as primary output"
    )


def test_valid_frontmatter() -> None:
    """agent/architect.md has valid YAML frontmatter without model: key."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")
    meta = parse_frontmatter(content, "architect.md")

    # Check required keys
    required_keys = ("description", "mode")
    for key in required_keys:
        assert key in meta, (
            f"architect.md: frontmatter missing required key {key!r} "
            f"(has: {sorted(meta)})"
        )

    # Check forbidden keys
    forbidden_keys = ("model",)
    for key in forbidden_keys:
        assert key not in meta, (
            f"architect.md: frontmatter must not contain {key!r} — models are "
            f"configured only in the local opencode.jsonc"
        )
