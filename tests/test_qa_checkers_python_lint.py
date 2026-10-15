"""Tests for the mypy, ruff, and black checker functions (story 27-03).

Every test uses ``tmp_path`` as a fake project root, writes a ``qa_config.json``
selecting the checker under test, installs a stub runner binary (fake ``mypy``
/ ``ruff`` / ``black``, Python script replaying preserved output) on ``PATH``
and invokes the real ``scripts/qa_compress.py`` from there. No real Python
linting toolchain is required — the stub binary is the external-system fake.

Preserved runner output shapes:

- mypy: error messages in the format ``FILE:LINE:COL: error: MESSAGE``.
  Summary line: ``Found N errors in M files`` (on failure).
- ruff: violation lines in the format ``FILE:LINE:COL: CODE MESSAGE``.
  Summary line: ``Found N errors`` (on failure).
- black: lists files that would be reformatted and the final line
  ``would reformat N file(s), N file(s) would be left unchanged``.
  On success: just returns without output or summary.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.py"


# Fake output for mypy
FAKE_MYPY_PASS_OUTPUT = ""
FAKE_MYPY_FAIL_OUTPUT = (
    "src/app.py:5:10: error: Incompatible types in assignment "
    "(expression has type \"int\", variable has type \"str\")\n"
    "src/config.py:12:3: error: Name 'undefined_var' is not defined\n"
    "src/utils.py:20:5: error: Argument 1 to \"len\" has incompatible type "
    "\"None\"; expected \"Sized\"\n"
    "Found 3 errors in 3 files\n"
)

# Fake output for ruff
FAKE_RUFF_PASS_OUTPUT = ""
FAKE_RUFF_FAIL_OUTPUT = (
    "src/app.py:1:1: F401 [*] `os` imported but unused\n"
    "src/app.py:5:1: E302 expected 2 blank lines, found 1\n"
    "src/config.py:10:80: E501 line too long (92 > 79 characters)\n"
    "Found 3 errors\n"
)

# Fake output for black
FAKE_BLACK_PASS_OUTPUT = ""
FAKE_BLACK_FAIL_OUTPUT = (
    "would reformat src/app.py\n"
    "would reformat src/config.py\n"
    "All done! 2 files would be reformatted.\n"
)


def _install_fake_runner(
    name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    output: str,
    exit_code: int = 0,
) -> None:
    """Install a stub ``name`` binary that replays ``output`` with ``exit_code``."""
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


# ============================================================================
# mypy tests
# ============================================================================

def test_mypy_check_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake mypy -> 'mypy: 0 errors', overall PASS."""
    _install_fake_runner("mypy", tmp_path, monkeypatch, FAKE_MYPY_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["mypy"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## mypy (exit: 0)" in result.stdout
    assert "mypy: 0 errors" in result.stdout
    assert "overall: PASS" in result.stdout


def test_mypy_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake mypy -> overall FAIL, error count and sample errors listed."""
    _install_fake_runner(
        "mypy", tmp_path, monkeypatch, FAKE_MYPY_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["mypy"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## mypy (exit: 1)" in result.stdout
    assert "3 errors" in result.stdout
    assert "error:" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_mypy_check_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing mypy -> exit 1, 'mypy not found'."""
    # Set PATH to a directory that doesn't contain mypy (empty tmp bin dir)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(bin_dir))
    _write_config(tmp_path, '{"checkers": ["mypy"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "mypy not found" in result.stdout
    assert "overall: FAIL" in result.stdout


# ============================================================================
# ruff tests
# ============================================================================

def test_ruff_check_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake ruff -> 'ruff: 0 violations', overall PASS."""
    _install_fake_runner("ruff", tmp_path, monkeypatch, FAKE_RUFF_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["ruff"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## ruff (exit: 0)" in result.stdout
    assert "ruff: 0 violations" in result.stdout
    assert "overall: PASS" in result.stdout


def test_ruff_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake ruff -> overall FAIL, violation lines listed."""
    _install_fake_runner(
        "ruff", tmp_path, monkeypatch, FAKE_RUFF_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["ruff"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## ruff (exit: 1)" in result.stdout
    assert "3 violations" in result.stdout
    assert "F401" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_ruff_check_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing ruff -> exit 1, 'ruff not found'."""
    # Set PATH to a directory that doesn't contain ruff (empty tmp bin dir)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(bin_dir))
    _write_config(tmp_path, '{"checkers": ["ruff"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "ruff not found" in result.stdout
    assert "overall: FAIL" in result.stdout


# ============================================================================
# black tests
# ============================================================================

def test_black_check_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake black -> 'black: all files formatted', overall PASS."""
    _install_fake_runner("black", tmp_path, monkeypatch, FAKE_BLACK_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["black"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## black (exit: 0)" in result.stdout
    assert "black: all files formatted" in result.stdout
    assert "overall: PASS" in result.stdout


def test_black_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake black -> overall FAIL, reformattable files listed."""
    _install_fake_runner(
        "black", tmp_path, monkeypatch, FAKE_BLACK_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["black"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## black (exit: 1)" in result.stdout
    assert "would reformat" in result.stdout
    assert "src/app.py" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_black_check_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing black -> exit 1, 'black not found'."""
    # Set PATH to a directory that doesn't contain black (empty tmp bin dir)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(bin_dir))
    _write_config(tmp_path, '{"checkers": ["black"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "black not found" in result.stdout
    assert "overall: FAIL" in result.stdout
