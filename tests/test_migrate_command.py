"""Tests for /migrate-project command (Story 12-01).

Checks:
1. command/migrate-project.md exists with correct frontmatter
2. agent field is 'architect'
3. description field is present and correct
4. Command references the migrate-project skill
5. Command accepts optional $ARGUMENTS

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


def test_migrate_project_command_exists() -> None:
    """command/migrate-project.md exists."""
    migrate_cmd_path = REPO_ROOT / "command" / "migrate-project.md"
    assert migrate_cmd_path.is_file(), f"missing {migrate_cmd_path.relative_to(REPO_ROOT)}"


def test_migrate_project_command_has_frontmatter() -> None:
    """command/migrate-project.md has required frontmatter fields."""
    migrate_cmd_path = REPO_ROOT / "command" / "migrate-project.md"
    assert migrate_cmd_path.is_file(), f"missing {migrate_cmd_path.relative_to(REPO_ROOT)}"

    content = migrate_cmd_path.read_text(encoding="utf-8")
    meta = parse_frontmatter(content, "migrate-project.md")

    required_keys = ("description", "agent")
    for key in required_keys:
        assert key in meta, (
            f"migrate-project.md: frontmatter missing required key {key!r} "
            f"(has: {sorted(meta)})"
        )


def test_migrate_project_command_agent_is_architect() -> None:
    """command/migrate-project.md agent field is 'architect'."""
    migrate_cmd_path = REPO_ROOT / "command" / "migrate-project.md"
    content = migrate_cmd_path.read_text(encoding="utf-8")
    meta = parse_frontmatter(content, "migrate-project.md")

    assert meta.get("agent") == "architect", (
        f"migrate-project.md: agent must be 'architect', got {meta.get('agent')!r}"
    )


def test_migrate_project_command_description() -> None:
    """command/migrate-project.md description is correct."""
    migrate_cmd_path = REPO_ROOT / "command" / "migrate-project.md"
    content = migrate_cmd_path.read_text(encoding="utf-8")
    meta = parse_frontmatter(content, "migrate-project.md")

    description = meta.get("description", "")
    assert "Migrate" in description or "migrate" in description, (
        f"migrate-project.md: description should mention 'Migrate', got {description!r}"
    )
    assert "project" in description.lower(), (
        f"migrate-project.md: description should mention 'project', got {description!r}"
    )


def test_migrate_project_command_references_skill() -> None:
    """command/migrate-project.md references the migrate-project skill."""
    migrate_cmd_path = REPO_ROOT / "command" / "migrate-project.md"
    content = migrate_cmd_path.read_text(encoding="utf-8")

    # Check that the command body references the skill
    assert "migrate-project" in content.lower(), (
        "migrate-project.md: command body should reference 'migrate-project' skill"
    )


def test_migrate_project_command_accepts_arguments() -> None:
    """command/migrate-project.md accepts optional $ARGUMENTS."""
    migrate_cmd_path = REPO_ROOT / "command" / "migrate-project.md"
    content = migrate_cmd_path.read_text(encoding="utf-8")

    # Check that the command body references $ARGUMENTS
    assert "$ARGUMENTS" in content, (
        "migrate-project.md: command body should reference '$ARGUMENTS' for optional path"
    )
