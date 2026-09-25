"""Tests for the qa_compress.py config contract (story 12-01).

Every test uses ``tmp_path`` as a fake project root, installs a stub runner
binary (fake pytest, Python script replaying preserved output) on PATH and
invokes the real ``scripts/qa_compress.py`` from there. No real pytest or
runner is required — the stub binary is the external-system fake.

The config contract (``qa_config.json`` in the project cwd):

- no config file        -> default ``["pytest"]`` (backward compatible)
- ``{"checkers": ["pytest"]}`` -> same behavior as default
- unknown checker name  -> loud FAIL: ``unknown checker: <name>``, exit 1
- ``{"checkers": []}``  -> explicit opt-out, overall PASS, exit 0
- invalid JSON          -> FAIL with an error message, exit 1 (no traceback)
- failing runner        -> aggregated overall FAIL, compact failure sections
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


FAKE_PYTEST_PASS_OUTPUT = (
    "============================= test session starts =============================\n"
    "collected 78 items\n"
    "\n"
    "tests/test_a.py ............................................................\n"
    "============================= 78 passed in 0.50s ==============================\n"
)
FAKE_PYTEST_FAIL_OUTPUT = (
    "============================= test session starts =============================\n"
    "================================== FAILURES ===================================\n"
    "___________________________________ test_a ____________________________________\n"
    "\n"
    ">       assert 1 == 2\n"
    "E       assert 1 == 2\n"
    "\n"
    "FAILED tests/x.py::test_a - assert 1 == 2\n"
    "============================== 1 failed in 0.77s ==============================\n"
)


def _install_fake_pytest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    output: str,
    exit_code: int = 0,
) -> None:
    """Install a stub ``pytest`` binary that replays ``output`` with ``exit_code``."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    # Create Python implementation
    py_script = bin_dir / "pytest_impl.py"
    py_script.write_text(
        "import sys, io\n"
        "sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')\n"
        "import sys\n"
        f"sys.stdout.write({repr(output)})\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )
    
    # Create .cmd wrapper for Windows (use sys.executable for python)
    cmd_wrapper = bin_dir / "pytest.cmd"
    cmd_wrapper.write_text(
        f'@"{sys.executable}" "{py_script}" %*\n',
        encoding="utf-8",
    )
    
    # Create shebang script for Unix
    script = bin_dir / "pytest"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import sys, io\n"
        "sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')\n"
        "import sys\n"
        f"sys.stdout.write({repr(output)})\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])


def _write_config(tmp_path: Path, content: str) -> None:
    (tmp_path / "qa_config.json").write_text(content, encoding="utf-8")


def _run_qa_compress(cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the real qa_compress.py from the fake project root."""
    return subprocess.run(
        [sys.executable, str(QA_SCRIPT)],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )


def test_default_pytest_without_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No qa_config.json -> default checker list ['pytest'] (backward compat)."""
    _install_fake_pytest(tmp_path, monkeypatch, FAKE_PYTEST_PASS_OUTPUT)
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## pytest" in result.stdout
    assert "overall: PASS" in result.stdout
    assert "78 passed" in result.stdout


def test_explicit_pytest_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Explicit ['pytest'] behaves identically to the default."""
    _install_fake_pytest(tmp_path, monkeypatch, FAKE_PYTEST_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["pytest"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## pytest" in result.stdout
    assert "overall: PASS" in result.stdout
    assert "78 passed" in result.stdout


def test_unknown_checker_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Configured checker with no registered plugin -> loud FAIL, exit 1."""
    _install_fake_pytest(tmp_path, monkeypatch, FAKE_PYTEST_PASS_OUTPUT)
    # NOTE: "rspec" became a real plugin in story 12-02 — use a name that is
    # guaranteed to never have a registered checker plugin.
    _write_config(tmp_path, '{"checkers": ["definitely-not-a-checker"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1
    assert "unknown checker: definitely-not-a-checker" in result.stdout + result.stderr
    # The registered (but not configured) pytest checker must NOT run.
    assert "## pytest" not in result.stdout


def test_empty_config_optout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Empty checker list -> explicit opt-out: overall PASS, exit 0."""
    _install_fake_pytest(tmp_path, monkeypatch, FAKE_PYTEST_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": []}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "no checkers configured (explicit opt-out)" in result.stdout
    assert "overall: PASS" in result.stdout
    assert "## pytest" not in result.stdout


def test_invalid_config_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid JSON in qa_config.json -> FAIL with error message, exit 1."""
    _install_fake_pytest(tmp_path, monkeypatch, FAKE_PYTEST_PASS_OUTPUT)
    _write_config(tmp_path, "{not valid json")
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    # A clear, non-empty error message (no raw Python traceback).
    assert combined.strip(), "expected a non-empty error message"
    assert "invalid" in combined.lower()
    assert "Traceback" not in combined


def test_fake_pytest_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failing fake pytest -> compact failure output, overall FAIL."""
    _install_fake_pytest(tmp_path, monkeypatch, FAKE_PYTEST_FAIL_OUTPUT, exit_code=1)
    _write_config(tmp_path, '{"checkers": ["pytest"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1
    assert "failed_tests" in result.stdout
    assert "tests/x.py::test_a" in result.stdout
    assert "overall: FAIL" in result.stdout