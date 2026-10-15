"""Tests for the eslint, tsc, prettier, and npm-audit checkers (story 27-02).

Every test uses ``tmp_path`` as a fake project root, writes a ``qa_config.json``
selecting the checker under test, installs a stub runner binary (fake ``eslint`` /
``tsc`` / ``prettier`` / ``npm``, Python script replaying preserved output) on
``PATH`` and invokes the real ``scripts/qa_compress.py`` from there. No real
JavaScript/TypeScript toolchain is required — the stub binary is the external-system
fake.

Preserved runner output shapes:

- eslint: "no problems" on success, error lines (file:line:col: message) on failure.
- tsc --noEmit: no output on success, error lines on failure.
- prettier --check: "All matched files use Prettier code style" on success, 
  list of unformatted files on failure.
- npm audit: "0 vulnerabilities" on success, vulnerability count on failure.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.py"


FAKE_ESLINT_PASS_OUTPUT = "0 problems\n"
FAKE_ESLINT_FAIL_OUTPUT = (
    "src/index.ts:5:10: 'foo' is assigned a value but never used. (no-unused-vars)\n"
    "src/index.ts:8:2: Missing semicolon. (semi)\n"
    "src/utils.ts:15:5: Unexpected console statement. (no-console)\n"
)

FAKE_TSC_PASS_OUTPUT = ""
FAKE_TSC_FAIL_OUTPUT = (
    "src/index.ts(5,10): error TS2304: Cannot find name 'foo'.\n"
    "src/utils.ts(8,2): error TS7030: Not all code paths return a value.\n"
)

FAKE_PRETTIER_PASS_OUTPUT = "All matched files use Prettier code style!\n"
FAKE_PRETTIER_FAIL_OUTPUT = (
    "src/index.ts\n"
    "src/component.tsx\n"
)

FAKE_NPM_AUDIT_PASS_OUTPUT = (
    "up to date\n"
    "0 vulnerabilities\n"
)
FAKE_NPM_AUDIT_FAIL_OUTPUT = (
    "found 3 vulnerabilities\n"
    "  1 high   in dependencies\n"
    "  2 moderate in devDependencies\n"
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
# ESLint tests
# ============================================================================


def test_eslint_check_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake eslint -> '0 errors' in output, overall PASS."""
    _install_fake_runner("eslint", tmp_path, monkeypatch, FAKE_ESLINT_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["eslint"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## eslint (exit: 0)" in result.stdout
    assert "0 errors" in result.stdout
    assert "overall: PASS" in result.stdout


def test_eslint_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake eslint with 3 errors -> overall FAIL, error lines present."""
    _install_fake_runner(
        "eslint", tmp_path, monkeypatch, FAKE_ESLINT_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["eslint"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## eslint (exit: 1)" in result.stdout
    assert "no-unused-vars" in result.stdout or "error" in result.stdout.lower()
    assert "overall: FAIL" in result.stdout


def test_eslint_check_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No eslint on PATH -> '(exit: 1)', 'not found' message present."""
    # Don't install eslint; path is empty
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(bin_dir))
    
    _write_config(tmp_path, '{"checkers": ["eslint"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## eslint (exit: 1)" in result.stdout
    assert "not found" in result.stdout.lower()
    assert "overall: FAIL" in result.stdout


# ============================================================================
# tsc tests
# ============================================================================


def test_tsc_check_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake tsc --noEmit -> '0 errors' in output, overall PASS."""
    _install_fake_runner("tsc", tmp_path, monkeypatch, FAKE_TSC_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["tsc"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## tsc (exit: 0)" in result.stdout
    assert "0 errors" in result.stdout
    assert "overall: PASS" in result.stdout


def test_tsc_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake tsc with TS errors -> overall FAIL, error lines present."""
    _install_fake_runner(
        "tsc", tmp_path, monkeypatch, FAKE_TSC_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["tsc"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## tsc (exit: 1)" in result.stdout
    assert "error TS" in result.stdout or "Cannot find name" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_tsc_check_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No tsc on PATH -> '(exit: 1)', 'not found' message present."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(bin_dir))
    
    _write_config(tmp_path, '{"checkers": ["tsc"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## tsc (exit: 1)" in result.stdout
    assert "not found" in result.stdout.lower()
    assert "overall: FAIL" in result.stdout


# ============================================================================
# Prettier tests
# ============================================================================


def test_prettier_check_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake prettier --check -> 'all files formatted' in output, overall PASS."""
    _install_fake_runner("prettier", tmp_path, monkeypatch, FAKE_PRETTIER_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["prettier"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## prettier (exit: 0)" in result.stdout
    assert "formatted" in result.stdout.lower()
    assert "overall: PASS" in result.stdout


def test_prettier_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake prettier with unformatted files -> overall FAIL, file list present."""
    _install_fake_runner(
        "prettier", tmp_path, monkeypatch, FAKE_PRETTIER_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["prettier"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## prettier (exit: 1)" in result.stdout
    assert "src/index.ts" in result.stdout or "unformatted" in result.stdout.lower()
    assert "overall: FAIL" in result.stdout


def test_prettier_check_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No prettier on PATH -> '(exit: 1)', 'not found' message present."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(bin_dir))
    
    _write_config(tmp_path, '{"checkers": ["prettier"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## prettier (exit: 1)" in result.stdout
    assert "not found" in result.stdout.lower()
    assert "overall: FAIL" in result.stdout


# ============================================================================
# npm-audit tests
# ============================================================================


def test_npm_audit_check_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake npm audit -> '0 high/critical' in output, overall PASS."""
    _install_fake_runner("npm", tmp_path, monkeypatch, FAKE_NPM_AUDIT_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["npm-audit"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## npm-audit (exit: 0)" in result.stdout
    assert "0 high" in result.stdout.lower() or "vulnerabilities" in result.stdout.lower()
    assert "overall: PASS" in result.stdout


def test_npm_audit_check_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake npm audit with vulnerabilities -> overall FAIL, summary present."""
    _install_fake_runner(
        "npm", tmp_path, monkeypatch, FAKE_NPM_AUDIT_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["npm-audit"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## npm-audit (exit: 1)" in result.stdout
    assert "3" in result.stdout or "high" in result.stdout.lower()
    assert "overall: FAIL" in result.stdout


def test_npm_audit_check_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No npm on PATH -> '(exit: 1)', 'not found' message present."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PATH", str(bin_dir))
    
    _write_config(tmp_path, '{"checkers": ["npm-audit"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## npm-audit (exit: 1)" in result.stdout
    assert "not found" in result.stdout.lower()
    assert "overall: FAIL" in result.stdout
