"""Tests for the gradle/maven checker plugins (story 12-03).

Every test uses ``tmp_path`` as a fake project root, installs a stub runner
binary (fake ``gradle`` / ``mvn``, Python script replaying preserved output,
correct exit codes) on PATH and invokes the real ``scripts/qa_compress.py``
from there. No real Gradle or Maven is required — the stub binary is the
external-system fake.

The checker contract (12-01): each checker is a self-registering plugin file
under ``scripts/qa_checkers/`` selected via ``qa_config.json``; the checker
prints a compressed result on stdout and returns the runner's exit code.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.py"


FAKE_GRADLE_PASS_OUTPUT = (
    "> Task :test\n"
    "\n"
    "12 tests completed, 0 failed\n"
    "\n"
    "BUILD SUCCESSFUL\n"
)
FAKE_GRADLE_FAIL_OUTPUT = (
    "> Task :test\n"
    "\n"
    "3 tests completed, 1 failed\n"
    "com.example.BoardTest > rendersBoard() FAILED\n"
    "BUILD FAILED\n"
)
FAKE_MAVEN_PASS_OUTPUT = (
    "Tests run: 8, Failures: 0, Errors: 0, Skipped: 0\n"
    "\n"
    "BUILD SUCCESS\n"
)
FAKE_MAVEN_FAIL_OUTPUT = (
    "Tests run: 3, Failures: 1, Errors: 0, Skipped: 0\n"
    "[ERROR] Tests run: 3, Failures: 1 ... in BoardTest\n"
    "BoardTest.rendersBoard:15 <<< FAILURE!\n"
    "BUILD FAILURE\n"
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


def test_gradle_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Green gradle run -> overall PASS, BUILD SUCCESSFUL summary."""
    _install_stub_runner(
        tmp_path, monkeypatch, "gradle", FAKE_GRADLE_PASS_OUTPUT, exit_code=0
    )
    _write_config(tmp_path, '{"checkers": ["gradle"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## gradle" in result.stdout
    assert "overall: PASS" in result.stdout
    assert "BUILD SUCCESSFUL" in result.stdout


def test_gradle_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing gradle run -> overall FAIL, failing test identifier listed."""
    _install_stub_runner(
        tmp_path, monkeypatch, "gradle", FAKE_GRADLE_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["gradle"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1
    assert "overall: FAIL" in result.stdout
    assert "## failed_tests" in result.stdout
    assert "com.example.BoardTest > rendersBoard() FAILED" in result.stdout
    # The BUILD line itself must not leak into the failed_tests section.
    failed_section = result.stdout.split("## failed_tests", 1)[1]
    assert "BUILD FAILED" not in failed_section


def test_maven_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green maven run -> overall PASS."""
    _install_stub_runner(
        tmp_path, monkeypatch, "mvn", FAKE_MAVEN_PASS_OUTPUT, exit_code=0
    )
    _write_config(tmp_path, '{"checkers": ["maven"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## maven" in result.stdout
    assert "overall: PASS" in result.stdout
    assert "Tests run: 8, Failures: 0" in result.stdout


def test_maven_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing maven run -> overall FAIL, failing test identifier listed."""
    _install_stub_runner(
        tmp_path, monkeypatch, "mvn", FAKE_MAVEN_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["maven"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1
    assert "overall: FAIL" in result.stdout
    assert "## failed_tests" in result.stdout
    failed_section = result.stdout.split("## failed_tests", 1)[1]
    assert "BoardTest.rendersBoard" in failed_section
    assert "Tests run: 3, Failures: 1" in result.stdout