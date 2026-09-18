"""Tests for promote_release.py script.

Test criteria (from story 06-03):
- test_script_exists: scripts/promote_release.py exists and is valid Python
- test_script_has_main_guard: script has if __name__ == "__main__" entry point
- test_readme_mentions_release_branch: README contains "release" branch documentation
- test_agents_md_mentions_release: AGENTS.md references "release" for deployment
"""

from __future__ import annotations

import py_compile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_script_exists() -> None:
    """scripts/promote_release.py exists and is valid Python (py_compile)."""
    script_path = REPO_ROOT / "scripts" / "promote_release.py"
    assert script_path.exists(), f"Script not found: {script_path}"
    
    # Verify it's valid Python by compiling it
    try:
        py_compile.compile(str(script_path), doraise=True)
    except py_compile.PyCompileError as e:
        raise AssertionError(f"Script is not valid Python: {e}") from e


def test_script_has_main_guard() -> None:
    """scripts/promote_release.py has if __name__ == "__main__" entry point."""
    script_path = REPO_ROOT / "scripts" / "promote_release.py"
    assert script_path.exists(), f"Script not found: {script_path}"
    
    content = script_path.read_text(encoding="utf-8")
    assert 'if __name__ == "__main__"' in content, (
        "Script must have 'if __name__ == \"__main__\"' entry point"
    )


def test_readme_mentions_release_branch() -> None:
    """README.md contains "release" branch documentation."""
    readme_path = REPO_ROOT / "README.md"
    assert readme_path.exists(), f"README not found: {readme_path}"
    
    content = readme_path.read_text(encoding="utf-8")
    assert "release" in content.lower(), (
        "README must document the release branch strategy"
    )


def test_agents_md_mentions_release() -> None:
    """AGENTS.md references 'release' for deployment."""
    agents_path = REPO_ROOT / "AGENTS.md"
    assert agents_path.exists(), f"AGENTS.md not found: {agents_path}"
    
    content = agents_path.read_text(encoding="utf-8")
    assert "release" in content.lower(), (
        "AGENTS.md must reference 'release' branch in deployment rules"
    )
