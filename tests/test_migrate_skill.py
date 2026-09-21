"""Tests for migrate-project skill (Story 12-01).

Checks:
1. skills/migrate-project.md exists
2. Skill contains all 6 migration phases
3. Skill references the expected script names
4. Skill instructs Architect to never modify source code

Stdlib only — no external systems, deterministic (repo files are the fixture).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_migrate_project_skill_exists() -> None:
    """skills/migrate-project.md exists."""
    skill_path = REPO_ROOT / "skills" / "migrate-project.md"
    assert skill_path.is_file(), f"missing {skill_path.relative_to(REPO_ROOT)}"


def test_migrate_project_skill_has_all_phases() -> None:
    """skills/migrate-project.md contains all 6 migration phases."""
    skill_path = REPO_ROOT / "skills" / "migrate-project.md"
    content = skill_path.read_text(encoding="utf-8")

    # Check for all 6 phases
    phases = [
        "Phase 1",
        "Phase 2",
        "Phase 3",
        "Phase 4",
        "Phase 5",
        "Phase 6",
    ]

    for phase in phases:
        assert phase in content, (
            f"migrate-project.md: missing {phase}"
        )


def test_migrate_project_skill_references_analyze_script() -> None:
    """skills/migrate-project.md references analyze_project.py script."""
    skill_path = REPO_ROOT / "skills" / "migrate-project.md"
    content = skill_path.read_text(encoding="utf-8")

    assert "analyze_project.py" in content, (
        "migrate-project.md: should reference 'analyze_project.py' script"
    )


def test_migrate_project_skill_references_provision_script() -> None:
    """skills/migrate-project.md references provision_structure.py script."""
    skill_path = REPO_ROOT / "skills" / "migrate-project.md"
    content = skill_path.read_text(encoding="utf-8")

    assert "provision_structure.py" in content, (
        "migrate-project.md: should reference 'provision_structure.py' script"
    )


def test_migrate_project_skill_references_validate_script() -> None:
    """skills/migrate-project.md references validate_migration.py script."""
    skill_path = REPO_ROOT / "skills" / "migrate-project.md"
    content = skill_path.read_text(encoding="utf-8")

    assert "validate_migration.py" in content, (
        "migrate-project.md: should reference 'validate_migration.py' script"
    )


def test_migrate_project_skill_references_prepare_agents_script() -> None:
    """skills/migrate-project.md references prepare_agents_md.py script."""
    skill_path = REPO_ROOT / "skills" / "migrate-project.md"
    content = skill_path.read_text(encoding="utf-8")

    assert "prepare_agents_md.py" in content, (
        "migrate-project.md: should reference 'prepare_agents_md.py' script"
    )


def test_migrate_project_skill_references_retro_stories_script() -> None:
    """skills/migrate-project.md references create_retro_stories.py script."""
    skill_path = REPO_ROOT / "skills" / "migrate-project.md"
    content = skill_path.read_text(encoding="utf-8")

    assert "create_retro_stories.py" in content, (
        "migrate-project.md: should reference 'create_retro_stories.py' script"
    )


def test_migrate_project_skill_warns_about_source_code() -> None:
    """skills/migrate-project.md instructs Architect to never modify source code."""
    skill_path = REPO_ROOT / "skills" / "migrate-project.md"
    content = skill_path.read_text(encoding="utf-8")

    # Check for warnings about not modifying source code
    content_lower = content.lower()
    assert ("source code" in content_lower or "src/" in content or "tests/" in content), (
        "migrate-project.md: should warn about not modifying source code"
    )
