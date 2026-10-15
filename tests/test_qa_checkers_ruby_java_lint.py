"""Tests for the rubocop and checkstyle checker functions (story 27-04).

Every test uses ``tmp_path`` as a fake project root, writes a ``qa_config.json``
selecting the checker under test, installs a stub runner binary (fake ``rubocop``,
``checkstyle``, ``gradlew``, or ``mvn``, Python script replaying preserved output)
on ``PATH`` and invokes the real ``scripts/qa_compress.py`` from there. No real
Ruby/Java toolchain is required — the stub binary is the external-system fake.

Preserved output shapes:
- rubocop: "0 offenses" on success, or list of offense lines on failure.
- checkstyle: "0 violations" on success, or list of violation lines on failure.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.py"


FAKE_RUBOCOP_PASS_OUTPUT = (
    "12 files inspected, no offenses detected\n"
)
FAKE_RUBOCOP_FAIL_OUTPUT = (
    "app/models/user.rb:5:2: C: Layout/IndentationStyle: Use 2 spaces\n"
    "app/models/post.rb:12:5: W: Metrics/MethodLength: exceeds 10\n"
)
FAKE_CHECKSTYLE_PASS_OUTPUT = (
    "BUILD SUCCESSFUL\n"
)
FAKE_CHECKSTYLE_FAIL_OUTPUT = (
    "[ERROR] /path/to/Main.java:10: Line exceeds 80 characters\n"
    "[ERROR] /path/to/Board.java:25: Missing javadoc\n"
)


def _install_stub_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    output: str,
    exit_code: int = 0,
) -> None:
    """Install a stub ``<name>`` binary that replays ``output`` with ``exit_code``."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    
    # Create Python implementation
    py_script = bin_dir / f"{name}_impl.py"
    py_script.write_text(
        "import sys, io\n"
        "sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')\n"
        "import sys\n"
        f"sys.stdout.write({repr(output)})\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )
    
    # Create .cmd wrapper for Windows (use sys.executable for python)
    cmd_wrapper = bin_dir / f"{name}.cmd"
    cmd_wrapper.write_text(
        f'@"{sys.executable}" "{py_script}" %*\n',
        encoding="utf-8",
    )
    
    # Create shebang script for Unix
    script = bin_dir / name
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


def test_rubocop_check_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake rubocop -> '0 offenses' summary, overall PASS."""
    _install_stub_runner(tmp_path, monkeypatch, "rubocop", FAKE_RUBOCOP_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["rubocop"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## rubocop (exit: 0)" in result.stdout
    assert "0 offenses" in result.stdout
    assert "overall: PASS" in result.stdout


def test_rubocop_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake rubocop -> overall FAIL, offense lines listed."""
    _install_stub_runner(
        tmp_path, monkeypatch, "rubocop", FAKE_RUBOCOP_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["rubocop"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## rubocop (exit: 1)" in result.stdout
    assert "overall: FAIL" in result.stdout
    assert "app/models/user.rb:5:2" in result.stdout


def test_rubocop_check_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No rubocop on PATH -> overall FAIL, 'not found' message."""
    # Set PATH to empty dir (no rubocop, no bundle)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(bin_dir))
    
    _write_config(tmp_path, '{"checkers": ["rubocop"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "overall: FAIL" in result.stdout
    assert "rubocop not found" in result.stdout


def test_checkstyle_check_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake gradlew checkstyle -> '0 violations' summary, overall PASS."""
    _install_stub_runner(tmp_path, monkeypatch, "gradlew", FAKE_CHECKSTYLE_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["checkstyle"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## checkstyle (exit: 0)" in result.stdout
    assert "0 violations" in result.stdout
    assert "overall: PASS" in result.stdout


def test_checkstyle_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake gradlew checkstyle -> overall FAIL, violation lines listed."""
    _install_stub_runner(
        tmp_path, monkeypatch, "gradlew", FAKE_CHECKSTYLE_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["checkstyle"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## checkstyle (exit: 1)" in result.stdout
    assert "overall: FAIL" in result.stdout
    assert "Main.java:10" in result.stdout


def test_checkstyle_check_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No gradlew/mvn/checkstyle -> overall FAIL, 'not found' message."""
    # Set PATH to empty dir (no tools)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(bin_dir))
    
    _write_config(tmp_path, '{"checkers": ["checkstyle"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "overall: FAIL" in result.stdout
    assert "checkstyle not found" in result.stdout
