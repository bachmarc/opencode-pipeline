"""Test suite for story 17-05: Prompts drop script paths, describe actions only.

Checks:
1. No prompt file (agent/*.md, skills/*.md) contains `scripts/` followed by a `.py` filename
2. Script names without path prefix may remain (e.g. `session_recovery.py` alone is allowed)
3. Only `scripts/` prefix before a `.py` filename must be removed
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = REPO_ROOT / "agent"
SKILLS_DIR = REPO_ROOT / "skills"

# Pattern to match `scripts/<name>.py` (with backticks or not)
SCRIPT_PATH_PATTERN = re.compile(r"scripts/[a-z_]+\.py")


def test_architect_md_no_script_paths() -> None:
    """agent/architect.md contains no `scripts/[a-z_]+\.py` pattern."""
    architect_path = AGENT_DIR / "architect.md"
    assert architect_path.exists(), f"{architect_path} not found"
    
    content = architect_path.read_text(encoding="utf-8")
    matches = SCRIPT_PATH_PATTERN.findall(content)
    
    assert not matches, (
        f"agent/architect.md contains script paths: {matches}"
    )


def test_developer_md_no_script_paths() -> None:
    """agent/developer.md contains no `scripts/[a-z_]+\.py` pattern."""
    developer_path = AGENT_DIR / "developer.md"
    assert developer_path.exists(), f"{developer_path} not found"
    
    content = developer_path.read_text(encoding="utf-8")
    matches = SCRIPT_PATH_PATTERN.findall(content)
    
    assert not matches, (
        f"agent/developer.md contains script paths: {matches}"
    )


def test_qa_manager_md_no_script_paths() -> None:
    """agent/qa-manager.md contains no `scripts/[a-z_]+\.py` pattern."""
    qa_manager_path = AGENT_DIR / "qa-manager.md"
    assert qa_manager_path.exists(), f"{qa_manager_path} not found"
    
    content = qa_manager_path.read_text(encoding="utf-8")
    matches = SCRIPT_PATH_PATTERN.findall(content)
    
    assert not matches, (
        f"agent/qa-manager.md contains script paths: {matches}"
    )


def test_documenter_md_no_script_paths() -> None:
    """agent/documenter.md contains no `scripts/[a-z_]+\.py` pattern."""
    documenter_path = AGENT_DIR / "documenter.md"
    assert documenter_path.exists(), f"{documenter_path} not found"
    
    content = documenter_path.read_text(encoding="utf-8")
    matches = SCRIPT_PATH_PATTERN.findall(content)
    
    assert not matches, (
        f"agent/documenter.md contains script paths: {matches}"
    )


def test_skills_no_script_paths() -> None:
    """All files matching skills/*.md contain no `scripts/[a-z_]+\.py` pattern."""
    if not SKILLS_DIR.exists():
        # Skills directory may not exist in all projects
        return
    
    skill_files = sorted(SKILLS_DIR.glob("*.md"))
    assert skill_files, "no skills/*.md files found"
    
    violations: list[str] = []
    for path in skill_files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        content = path.read_text(encoding="utf-8")
        matches = SCRIPT_PATH_PATTERN.findall(content)
        if matches:
            violations.append(f"{rel}: {matches}")
    
    assert not violations, (
        f"skills/*.md files contain script paths:\n" + "\n".join(violations)
    )
