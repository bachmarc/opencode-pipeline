"""Tests for the JSON + YAML checker plugins (story 12-04).

Every test uses ``tmp_path`` as a fake project root with a ``qa_config.json``
and invokes the real ``scripts/qa_compress.sh`` from there. No stub is needed
for tests 1-5: the checkers validate files via ``python3`` one-liners and the
real python3 runs (PyYAML is available in this environment). The external-
system fake is the tmp_path project root itself.

Exclusions (deterministic contract, no gitignore parsing): the walk skips
``.git``, ``.pipeline``, ``.worktrees``, ``node_modules``, ``__pycache__``,
``.pytest_cache``, ``dist`` and ``build`` — and the pipeline's own
``qa_config.json`` (already validated by the dispatcher, not project payload).

``test_yaml_missing_pyyaml`` is the loud-failure path: it sources the yaml
plugin directly and calls ``yaml_check`` with a stub ``python3`` on PATH that
fails ONLY on ``import yaml`` (all other invocations delegate to the real
python3), so the dispatch in qa_compress.sh is not shadowed.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.sh"
YAML_PLUGIN = REPO_ROOT / "scripts" / "qa_checkers" / "yaml.sh"


def _write_config(tmp_path: Path, checkers: list[str]) -> None:
    (tmp_path / "qa_config.json").write_text(
        '{"checkers": ' + repr(checkers).replace("'", '"') + "}",
        encoding="utf-8",
    )


def _run_qa_compress(cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the real qa_compress.sh from the fake project root."""
    return subprocess.run(
        ["bash", str(QA_SCRIPT)],
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
    stub_dir = tmp_path / "stubbin"
    stub_dir.mkdir()
    # Stub python3: fails ONLY on `import yaml` (checker one-liner); every other
    # invocation delegates to the real python3, so nothing else is shadowed.
    stub = stub_dir / "python3"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        'case "$*" in\n'
        '  *"import yaml"*)\n'
        '    echo "Traceback: ModuleNotFoundError: No module named \'yaml\'" >&2\n'
        "    exit 1\n"
        "    ;;\n"
        "  *)\n"
        '    exec /usr/bin/python3 "$@"\n'
        "    ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)

    yaml_file = tmp_path / "feature.yml"
    yaml_file.write_text("key: value\n", encoding="utf-8")

    script = tmp_path / "run_yaml_check.sh"
    script.write_text(
        "#!/usr/bin/env bash\n"
        f'source "{YAML_PLUGIN}"\n'
        "cd " + str(tmp_path) + "\n"
        "yaml_check\n",
        encoding="utf-8",
    )
    script.chmod(0o755)

    result = subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env={**os.environ, "PATH": str(stub_dir) + os.pathsep + os.environ["PATH"]},
    )

    assert result.returncode == 1
    assert "yaml checker: PyYAML not installed" in result.stdout
    assert "## failed_files" not in result.stdout