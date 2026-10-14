"""
tests/test_v2_agent_dir.py
Story 24-01 — V2 Agent Directory Fix

Verifies that:
- agents/ (plural) directory exists (V2 convention)
- agent/  (singular) directory does NOT exist (V1 leftovers removed)
- Exactly four files are present in agents/
- None of the four files contains a deprecated temperature: frontmatter key
- Each file still has the required description: and mode: keys
"""
import os
import yaml
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(REPO_ROOT, "agents")
AGENT_DIR_V1 = os.path.join(REPO_ROOT, "agent")
EXPECTED_FILES = {"architect.md", "developer.md", "qa-manager.md", "documenter.md"}


def _parse_frontmatter(path: str) -> dict:
    """Return the YAML frontmatter dict from a Markdown file."""
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def test_agents_dir_exists():
    """agents/ (plural) directory must exist — V2 discovery path."""
    assert os.path.isdir(AGENTS_DIR), (
        f"Directory 'agents/' not found at {AGENTS_DIR}. "
        "OpenCode V2 requires plural 'agents/', not 'agent/'."
    )


def test_agent_dir_gone():
    """agent/ (singular, V1) directory must NOT exist."""
    assert not os.path.exists(AGENT_DIR_V1), (
        f"Legacy 'agent/' directory still exists at {AGENT_DIR_V1}. "
        "Remove it — OpenCode V2 only reads 'agents/'."
    )


def test_four_agent_files():
    """agents/ must contain exactly the four pipeline agent files."""
    if not os.path.isdir(AGENTS_DIR):
        pytest.skip("agents/ does not exist — covered by test_agents_dir_exists")
    found = {f for f in os.listdir(AGENTS_DIR) if f.endswith(".md")}
    assert found == EXPECTED_FILES, (
        f"Expected exactly {EXPECTED_FILES}, got {found}"
    )


@pytest.mark.parametrize("filename", sorted(EXPECTED_FILES))
def test_no_temperature_in_frontmatter(filename):
    """No agent file may contain a deprecated temperature: frontmatter key."""
    if not os.path.isdir(AGENTS_DIR):
        pytest.skip("agents/ does not exist")
    path = os.path.join(AGENTS_DIR, filename)
    fm = _parse_frontmatter(path)
    assert "temperature" not in fm, (
        f"{filename}: 'temperature' is a deprecated V1 frontmatter field. Remove it."
    )


@pytest.mark.parametrize("filename", sorted(EXPECTED_FILES))
def test_description_and_mode_present(filename):
    """Each agent file must retain description: and mode: frontmatter keys."""
    if not os.path.isdir(AGENTS_DIR):
        pytest.skip("agents/ does not exist")
    path = os.path.join(AGENTS_DIR, filename)
    fm = _parse_frontmatter(path)
    assert "description" in fm, f"{filename}: missing 'description' frontmatter key"
    assert "mode" in fm, f"{filename}: missing 'mode' frontmatter key"
