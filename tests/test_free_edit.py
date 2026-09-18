"""Tests for free-edit rule on user-facing docs (Story 07-03).

Validates:
1. The free-edit rule is documented in docs/design.md
2. README-content prose tests have been removed from the test suite
3. Internal/derived docs remain governed

This test suite ensures that user-facing docs (README.md) are free-edit
(no story/test criteria required), while internal/derived docs stay governed.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_design_md_documents_free_edit_rule() -> None:
    """docs/design.md contains the free-edit rule for user-facing docs."""
    design_path = REPO_ROOT / "docs" / "design.md"
    assert design_path.is_file(), f"design.md not found at {design_path}"

    content = design_path.read_text(encoding="utf-8")

    # Find README Structure section
    readme_structure_start = content.lower().find("readme structure")
    assert readme_structure_start != -1, "README Structure section not found in design.md"

    # Find next top-level section (##)
    next_section = content.find("\n## ", readme_structure_start + 1)
    if next_section == -1:
        readme_structure_section = content[readme_structure_start:]
    else:
        readme_structure_section = content[readme_structure_start:next_section]

    # Check for free-edit mention
    assert "free-edit" in readme_structure_section.lower(), (
        "design.md README Structure section does not mention 'free-edit'"
    )

    # Check for user-facing vs governed split
    section_lower = readme_structure_section.lower()
    has_user_facing = "user-facing" in section_lower or "user facing" in section_lower
    has_governed = "governed" in section_lower

    assert has_user_facing, (
        "design.md README Structure section does not mention 'user-facing' docs"
    )
    assert has_governed, (
        "design.md README Structure section does not mention 'governed' docs"
    )


def test_readme_structure_test_removed() -> None:
    """tests/test_readme_structure.py has been removed."""
    test_path = REPO_ROOT / "tests" / "test_readme_structure.py"
    assert not test_path.exists(), (
        "test_readme_structure.py should be deleted (README prose tests are free-edit)"
    )


def test_readme_deployment_test_removed() -> None:
    """tests/test_deploy_docs.py has been removed or is empty."""
    test_path = REPO_ROOT / "tests" / "test_deploy_docs.py"

    if test_path.exists():
        content = test_path.read_text(encoding="utf-8")
        # If the file exists, it must not contain test_readme_deployment_section
        assert "test_readme_deployment_section" not in content, (
            "test_deploy_docs.py still contains test_readme_deployment_section"
        )
        # If it only had that one test, the file should be gone
        # Count function definitions (def test_)
        test_count = content.count("def test_")
        assert test_count == 0, (
            f"test_deploy_docs.py should be deleted if empty, but has {test_count} test(s)"
        )


def test_readme_plugin_test_removed() -> None:
    """tests/test_prompt_integration.py no longer contains test_readme_mentions_plugin."""
    test_path = REPO_ROOT / "tests" / "test_prompt_integration.py"
    assert test_path.exists(), f"test_prompt_integration.py not found at {test_path}"

    content = test_path.read_text(encoding="utf-8")

    # The README-content test should be gone
    assert "test_readme_mentions_plugin" not in content, (
        "test_prompt_integration.py still contains test_readme_mentions_plugin"
    )

    # But the agent-file tests should remain
    assert "test_architect_prompt_mentions_plugin" in content, (
        "test_prompt_integration.py should still have test_architect_prompt_mentions_plugin"
    )
    assert "test_agents_md_documents_plugin" in content, (
        "test_prompt_integration.py should still have test_agents_md_documents_plugin"
    )


def test_readme_release_test_removed() -> None:
    """tests/test_promote_release.py no longer contains test_readme_mentions_release_branch."""
    test_path = REPO_ROOT / "tests" / "test_promote_release.py"
    assert test_path.exists(), f"test_promote_release.py not found at {test_path}"

    content = test_path.read_text(encoding="utf-8")

    # The README-content test should be gone
    assert "test_readme_mentions_release_branch" not in content, (
        "test_promote_release.py still contains test_readme_mentions_release_branch"
    )

    # But the script/agent tests should remain
    assert "test_script_exists" in content, (
        "test_promote_release.py should still have test_script_exists"
    )
    assert "test_script_has_main_guard" in content, (
        "test_promote_release.py should still have test_script_has_main_guard"
    )
    assert "test_agents_md_mentions_release" in content, (
        "test_promote_release.py should still have test_agents_md_mentions_release"
    )
