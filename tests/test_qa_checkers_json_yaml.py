"""Tests for the JSON + YAML checker plugins (story 12-04).

Every test uses ``tmp_path`` as a fake project root with a ``qa_config.json``
and invokes the real ``scripts/qa_compress.py`` from there. No stub is needed
for tests 1-5: the checkers validate files via Python and the real python3 runs
(PyYAML is available in this environment). The external-system fake is the
tmp_path project root itself.

Exclusions (deterministic contract, no gitignore parsing): the walk skips
``.git``, ``.pipeline``, ``.worktrees``, ``node_modules``, ``__pycache__``,
``.pytest_cache``, ``dist`` and ``build`` — and the pipeline's own
``qa_config.json`` (already validated by the dispatcher, not project payload).

``test_yaml_missing_pyyaml`` is the loud-failure path: it calls qa_compress.py
with a stub ``yaml`` module on PYTHONPATH that raises ImportError, so the
yaml checker fails loudly with "PyYAML not installed".
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.py"


def _write_config(tmp_path: Path, checkers: list[str]) -> None:
    (tmp_path / "qa_config.json").write_text(
        '{"checkers": ' + repr(checkers).replace("'", '"') + "}",
        encoding="utf-8",
    )


def _run_qa_compress(cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the real qa_compress.py from the fake project root."""
    return subprocess.run(
        [sys.executable, str(QA_SCRIPT)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_json_pass(tmp_path: Path) -> None:
    """Valid JSON project -> json checker PASS with '2 files checked, 0 invalid'."""
    _write_config(tmp_path, ["json"])
    (tmp_path / "cfg.json").write_text('{"a": 1}', encoding="utf-8")
    nested = tmp_path / "data"
    nested.mkdir()
    (nested / "nested.json").write_text('[1, 2, {"b": null}]', encoding="utf-8")

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## json (exit: 0)" in result.stdout
    assert "2 files checked, 0 invalid" in result.stdout
    assert "overall: PASS" in result.stdout
    assert "INVALID" not in result.stdout


def test_json_fail(tmp_path: Path) -> None:
    """One broken JSON file -> FAIL, INVALID path under ## failed_files."""
    _write_config(tmp_path, ["json"])
    (tmp_path / "cfg.json").write_text('{"a": 1}', encoding="utf-8")
    (tmp_path / "broken.json").write_text('{"a": 1', encoding="utf-8")

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout
    assert "## failed_files" in result.stdout
    assert "INVALID broken.json" in result.stdout
    assert "2 files checked, 1 invalid" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_json_excludes_pipeline_dirs(tmp_path: Path) -> None:
    """Broken JSON inside .worktrees/ is NOT walked -> checker still PASS."""
    _write_config(tmp_path, ["json"])
    (tmp_path / "cfg.json").write_text('{"a": 1}', encoding="utf-8")
    wt = tmp_path / ".worktrees" / "x"
    wt.mkdir(parents=True)
    (wt / "broken.json").write_text("{not json", encoding="utf-8")

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 files checked, 0 invalid" in result.stdout
    assert "INVALID" not in result.stdout
    assert "overall: PASS" in result.stdout


def test_yaml_pass(tmp_path: Path) -> None:
    """Valid feature.md-style frontmatter YAML -> yaml checker PASS."""
    _write_config(tmp_path, ["yaml"])
    _write_config(tmp_path, ["yaml"])
    # feature.md-style frontmatter, but as a single YAML document (leading
    # --- only): a trailing --- would open a second, empty document and
    # yaml.safe_load rejects multi-document input by contract.
    frontmatter = (
        "---\n"
        "id: F-008\n"
        "title: polyglot-qa\n"
        "stories:\n"
        "  - 12-04\n"
        "tags: [qa, checkers]\n"
    )
    (tmp_path / "frontmatter.yaml").write_text(frontmatter, encoding="utf-8")
    (tmp_path / "other.yml").write_text("key: [1, 2]\n", encoding="utf-8")

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## yaml (exit: 0)" in result.stdout
    assert "2 files checked, 0 invalid" in result.stdout
    assert "overall: PASS" in result.stdout


def test_yaml_fail(tmp_path: Path) -> None:
    """Broken YAML (bad indentation / unclosed flow) -> FAIL, INVALID listed."""
    _write_config(tmp_path, ["yaml"])
    (tmp_path / "good.yml").write_text("key: value\n", encoding="utf-8")
    (tmp_path / "broken.yml").write_text("key: [unclosed\n", encoding="utf-8")

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout
    assert "## failed_files" in result.stdout
    assert "INVALID broken.yml" in result.stdout
    assert "2 files checked, 1 invalid" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_yaml_missing_pyyaml(tmp_path: Path) -> None:
    """yaml import fails -> loud FAIL 'PyYAML not installed', exit 1 (no skip)."""
    # Create a fake yaml module that raises ImportError
    fake_yaml_dir = tmp_path / "fake_modules"
    fake_yaml_dir.mkdir()
    
    # Create a yaml.py that raises ImportError
    fake_yaml = fake_yaml_dir / "yaml.py"
    fake_yaml.write_text(
        "raise ImportError('No module named yaml')\n",
        encoding="utf-8",
    )
    
    # Create a YAML file to check
    yaml_file = tmp_path / "feature.yml"
    yaml_file.write_text("key: value\n", encoding="utf-8")
    
    # Write config
    _write_config(tmp_path, ["yaml"])
    
    # Run qa_compress.py with the fake yaml module on PYTHONPATH
    result = subprocess.run(
        [sys.executable, str(QA_SCRIPT)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env={
            **os.environ,
            "PYTHONPATH": str(fake_yaml_dir) + os.pathsep + os.environ.get("PYTHONPATH", ""),
        },
    )
    
    assert result.returncode == 1
    assert "yaml checker: PyYAML not installed" in result.stdout
    assert "## failed_files" not in result.stdout