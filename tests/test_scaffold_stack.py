"""Tests for scaffold_project.py --stack flag + repo qa_config.json (story 12-08).

The scaffold must be deterministic and flag-driven: no stack guessing. Each
stack maps to a fixed directory set, and every scaffolded project gets a
``qa_config.json`` (default ``{"checkers": ["pytest"]}``). The repo itself
dogfoods the gate with its own root ``qa_config.json``.

Every test targets ``tmp_path`` — no real external systems involved.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "scaffold_project.py"


def _scaffold(target, *flags):
    """Run the real scaffold script against target."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(target), *flags],
        capture_output=True,
        text=True,
        check=False,
    )


def test_scaffold_default_python(tmp_path):
    """No --stack flag -> python layout + qa_config.json default."""
    target = tmp_path / "proj_python"
    target.mkdir()

    result = _scaffold(target)
    assert result.returncode == 0, f"Scaffold failed: {result.stderr}"

    for dir_name in ("tests/fakes", "src/core", "src/adapters"):
        assert (target / dir_name).is_dir(), f"Directory {dir_name} not created"

    cfg_file = target / "qa_config.json"
    assert cfg_file.is_file(), "qa_config.json not created"
    assert json.loads(cfg_file.read_text(encoding="utf-8")) == {"checkers": ["pytest"]}


def test_scaffold_stack_ruby(tmp_path):
    """--stack ruby -> spec/ layout, no python-only src/core."""
    target = tmp_path / "proj_ruby"
    target.mkdir()

    result = _scaffold(target, "--stack", "ruby")
    assert result.returncode == 0, f"Scaffold failed: {result.stderr}"

    assert (target / "spec").is_dir(), "Directory spec/ not created"
    assert not (target / "src/core").exists(), "src/core must not exist for ruby"

    cfg_file = target / "qa_config.json"
    assert cfg_file.is_file(), "qa_config.json not created for ruby"


def test_scaffold_stack_java(tmp_path):
    """--stack java -> src/main + src/test, no tests/ dir."""
    target = tmp_path / "proj_java"
    target.mkdir()

    result = _scaffold(target, "--stack", "java")
    assert result.returncode == 0, f"Scaffold failed: {result.stderr}"

    assert (target / "src/main").is_dir(), "Directory src/main not created"
    assert (target / "src/test").is_dir(), "Directory src/test not created"
    assert not (target / "tests").exists(), "tests/ dir must not exist for java"


def test_scaffold_stack_mixed(tmp_path):
    """--stack mixed -> docs/ + src/ + tests/ only (no src/core)."""
    target = tmp_path / "proj_mixed"
    target.mkdir()

    result = _scaffold(target, "--stack", "mixed")
    assert result.returncode == 0, f"Scaffold failed: {result.stderr}"

    for dir_name in ("docs", "src", "tests"):
        assert (target / dir_name).is_dir(), f"Directory {dir_name} not created"
    assert not (target / "src/core").exists(), "src/core must not exist for mixed"


def test_qa_config_committed():
    """The repo's own root qa_config.json parses with the expected checkers."""
    cfg_file = REPO_ROOT / "qa_config.json"
    assert cfg_file.is_file(), "repo-root qa_config.json missing"

    data = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert data["checkers"] == ["pytest", "yaml"]