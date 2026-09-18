"""Tests for prompt integration with pipeline-enforcement plugin (Story 11-06).

Checks:
1. agent/architect.md mentions "pipeline-enforcement" or "enforcement plugin"
2. AGENTS.md documents "plugins/pipeline-enforcement"
3. README.md mentions "enforcement" or "plugin"

Stdlib only — no external systems, deterministic (repo files are the fixture).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_architect_prompt_mentions_plugin() -> None:
    """agent/architect.md contains reference to enforcement plugin."""
    architect_path = REPO_ROOT / "agent" / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"

    content = architect_path.read_text(encoding="utf-8")

    # Check for plugin references
    plugin_indicators = [
        "pipeline-enforcement",
        "enforcement plugin",
    ]

    found_plugin_reference = False
    for indicator in plugin_indicators:
        if indicator.lower() in content.lower():
            found_plugin_reference = True
            break

    assert found_plugin_reference, (
        "architect.md: does not mention pipeline-enforcement plugin"
    )


def test_agents_md_documents_plugin() -> None:
    """AGENTS.md contains documentation of plugins/pipeline-enforcement."""
    agents_path = REPO_ROOT / "AGENTS.md"
    assert agents_path.is_file(), f"missing {agents_path.relative_to(REPO_ROOT)}"

    content = agents_path.read_text(encoding="utf-8")

    assert "plugins/pipeline-enforcement" in content, (
        "AGENTS.md: does not mention plugins/pipeline-enforcement"
    )


def test_readme_mentions_plugin() -> None:
    """README.md mentions enforcement or plugin."""
    readme_path = REPO_ROOT / "README.md"
    assert readme_path.is_file(), f"missing {readme_path.relative_to(REPO_ROOT)}"

    content = readme_path.read_text(encoding="utf-8")

    # Check for plugin references
    plugin_indicators = [
        "enforcement",
        "pipeline-enforcement",
    ]

    found_plugin_reference = False
    for indicator in plugin_indicators:
        if indicator.lower() in content.lower():
            found_plugin_reference = True
            break

    assert found_plugin_reference, (
        "README.md: does not mention enforcement or pipeline-enforcement"
    )
