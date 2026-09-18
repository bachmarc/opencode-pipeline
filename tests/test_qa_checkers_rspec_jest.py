"""Tests for the rspec and jest checker plugins (story 12-02).

Every test uses ``tmp_path`` as a fake project root, writes a ``qa_config.json``
selecting the checker under test, installs a stub runner binary (fake ``rspec``
/ ``jest``, bash script replaying preserved output) on ``PATH`` and invokes the
real ``scripts/qa_compress.sh`` from there. No real Ruby/JavaScript toolchain
is required — the stub binary is the external-system fake.

Preserved runner output shapes:

- rspec ``--format progress``: progress dots, blank line,
  ``<N> examples, <M> failures`` summary; on failure a trailing list of
  ``rspec ./spec/...rb:LINE # description`` lines.
- jest: ``Tests:       <X failed, Y passed, Z total>`` summary; on failure
  ``✕ <test name> (<duration>)`` lines in the per-test results.

Both plugins are self-registering per the 12-01 plugin contract
(``scripts/qa_checkers/*.sh`` + ``register_check``); the checker exit code is
the runner's exit code, and ``qa_compress.sh`` aggregates overall PASS/FAIL.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.sh"


FAKE_RSPEC_PASS_OUTPUT = (
    "..........\n"
    "\n"
    "47 examples, 0 failures\n"
)
FAKE_RSPEC_FAIL_OUTPUT = (
    "F.\n"
    "\n"
    "2 examples, 1 failure\n"
    "\n"
    "Failed examples:\n"
    "\n"
    "rspec ./spec/board_spec.rb:12 # does a thing\n"
)
FAKE_JEST_PASS_OUTPUT = (
    "PASS src/board.test.ts\n"
    "  board\n"
    "    ✓ renders the board (3 ms)\n"
    "\n"
    "Test Suites: 1 passed, 1 total\n"
    "Tests:       4 passed, 4 total\n"
)
FAKE_JEST_FAIL_OUTPUT = (
    "FAIL src/board.test.ts\n"
    "  board\n"
    "    ✓ renders the header (2 ms)\n"
    "    ✓ clears the board (1 ms)\n"
    "    ✓ counts cells (1 ms)\n"
    "\n"
    "Test Suites: 1 failed, 1 total\n"
    "Tests:       1 failed, 3 passed, 4 total\n"
    "\n"
    "✕ renders the board (3 ms)\n"
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
    script = bin_dir / name
    script.write_text(
        "#!/usr/bin/env bash\n"
        "cat <<'FAKE_RUNNER_EOF'\n"
        f"{output}"
        "FAKE_RUNNER_EOF\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])


def _write_config(tmp_path: Path, content: str) -> None:
    (tmp_path / "qa_config.json").write_text(content, encoding="utf-8")


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


def test_rspec_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake rspec -> summary line + '## rspec (exit: 0)', overall PASS."""
    _install_fake_runner("rspec", tmp_path, monkeypatch, FAKE_RSPEC_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["rspec"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## rspec (exit: 0)" in result.stdout
    assert "47 examples, 0 failures" in result.stdout
    assert "overall: PASS" in result.stdout


def test_rspec_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake rspec -> overall FAIL, failed spec file:line listed."""
    _install_fake_runner(
        "rspec", tmp_path, monkeypatch, FAKE_RSPEC_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["rspec"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## rspec (exit: 1)" in result.stdout
    assert "2 examples, 1 failure" in result.stdout
    assert "./spec/board_spec.rb:12" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_jest_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Green fake jest -> 'Tests:' summary line present, overall PASS."""
    _install_fake_runner("jest", tmp_path, monkeypatch, FAKE_JEST_PASS_OUTPUT)
    _write_config(tmp_path, '{"checkers": ["jest"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## jest (exit: 0)" in result.stdout
    assert "Tests:       4 passed, 4 total" in result.stdout
    assert "overall: PASS" in result.stdout


def test_jest_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failing fake jest -> overall FAIL, failing test names (✕) listed."""
    _install_fake_runner(
        "jest", tmp_path, monkeypatch, FAKE_JEST_FAIL_OUTPUT, exit_code=1
    )
    _write_config(tmp_path, '{"checkers": ["jest"]}')
    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## jest (exit: 1)" in result.stdout
    assert "Tests:       1 failed, 3 passed, 4 total" in result.stdout
    assert "✕ renders the board" in result.stdout
    assert "overall: FAIL" in result.stdout