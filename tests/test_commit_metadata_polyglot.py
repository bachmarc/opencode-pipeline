"""Tests for the polyglot commit metadata script (story 12-06).

Every test uses ``tmp_path`` as a fake project root, creates a git repo there,
stages files, optionally writes a ``qa_config.json`` and installs stub runner
binaries (fake ``rspec`` / ``jest`` bash scripts replaying preserved output)
on ``PATH`` — then invokes the real ``scripts/prepare_commit_metadata.py``.
No real Ruby/JavaScript/Java toolchain is required — the stub binary is the
external-system fake.

Config contract (source of truth: ``qa_config.json`` in the repo root, same
default logic as story 12-01):

- no config file        -> default ``["pytest"]`` (backward compatible)
- ``{"checkers": [...]}`` -> first test-runner checker in the precedence order
  ``rspec, jest, gradle, maven, pytest`` wins; syntax checkers (``json``,
  ``yaml``, ``html``) never provide ``tests:``.

Output format contract: ``symbols: ... | breaks: ... | affects: ... |
tests: ...`` — exactly 4 pipe-separated sections (unchanged).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMIT_METADATA_SCRIPT = REPO_ROOT / "scripts" / "prepare_commit_metadata.py"


def _init_repo(repo_dir: Path) -> None:
    """Initialize a git repo with user config (quiet, deterministic)."""
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        capture_output=True,
    )


def _write_config(repo_dir: Path, checkers: list[str]) -> None:
    """Write qa_config.json with the given checker list into the repo root."""
    import json

    (repo_dir / "qa_config.json").write_text(
        json.dumps({"checkers": checkers}), encoding="utf-8"
    )


def _install_fake_runner(
    name: str,
    repo_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    output: str,
    exit_code: int = 0,
) -> None:
    """Install a stub ``name`` binary on PATH that replays ``output``."""
    bin_dir = repo_dir / "bin"
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


def _run_script(repo_dir: Path) -> subprocess.CompletedProcess[str]:
    """Run the real prepare_commit_metadata.py from the fake project root."""
    return subprocess.run(
        [sys.executable, str(COMMIT_METADATA_SCRIPT)],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_default_python_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No config + staged mod.py with def run() + stub 'python' -> pytest run."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)
    (repo_dir / "mod.py").write_text("def run():\n    pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "mod.py"], cwd=repo_dir, capture_output=True)
    # Stub `python` on PATH: replay a preserved pytest summary. The script must
    # invoke the runner (so `tests:` is non-empty) — either via the stubbed
    # `python` binary or via the real interpreter; both produce a summary.
    _install_fake_runner("python", repo_dir, monkeypatch, "3 passed\n")

    result = _run_script(repo_dir)

    assert result.returncode == 0, result.stderr
    output = result.stdout.strip()
    assert "symbols: run" in output, f"symbols must contain 'run':\n{output}"
    parts = output.split("|")
    assert len(parts) == 4, f"Expected 4 sections, got: {output}"
    tests_part = parts[3].strip()
    assert tests_part.startswith("tests:"), output
    assert tests_part != "tests: unknown", f"summary missing: {output}"


def test_rspec_symbols_and_tests(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Config ['rspec'] + staged board.rb -> ruby symbols + fake rspec tests."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)
    _write_config(repo_dir, ["rspec"])
    (repo_dir / "board.rb").write_text(
        "class Board\n"
        "  def move\n"
        "    true\n"
        "  end\n"
        "end\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "board.rb"], cwd=repo_dir, capture_output=True)
    _install_fake_runner("rspec", repo_dir, monkeypatch, "10 examples, 0 failures\n")

    result = _run_script(repo_dir)

    assert result.returncode == 0, result.stderr
    output = result.stdout.strip()
    assert "Board" in output and "move" in output, f"symbols missing:\n{output}"
    assert "10 examples, 0 failures" in output, f"tests missing rspec summary:\n{output}"


def test_js_symbols(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Config ['jest'] + staged render.js with function render() -> 'render'."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)
    _write_config(repo_dir, ["jest"])
    (repo_dir / "render.js").write_text(
        "function render() {}\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "render.js"], cwd=repo_dir, capture_output=True)
    _install_fake_runner(
        "jest", repo_dir, monkeypatch, "Tests:       2 passed, 2 total\n"
    )

    result = _run_script(repo_dir)

    assert result.returncode == 0, result.stderr
    output = result.stdout.strip()
    assert "symbols: render" in output, f"symbols must contain 'render':\n{output}"


def test_java_symbols(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Config ['maven'] + staged Board.java with class Board -> 'Board'."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)
    _write_config(repo_dir, ["maven"])
    (repo_dir / "Board.java").write_text(
        "public class Board {\n"
        "    private int width;\n"
        "}\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "Board.java"], cwd=repo_dir, capture_output=True)
    _install_fake_runner(
        "mvn", repo_dir, monkeypatch, "Tests run: 5, Failures: 0, Errors: 0\n"
    )

    result = _run_script(repo_dir)

    assert result.returncode == 0, result.stderr
    output = result.stdout.strip()
    assert "symbols: Board" in output, f"symbols must contain 'Board':\n{output}"


def test_syntax_only_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Config ['json', 'yaml'] + valid cfg.json -> tests: n/a (syntax only)."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)
    _write_config(repo_dir, ["json", "yaml"])
    (repo_dir / "cfg.json").write_text('{"valid": true}\n', encoding="utf-8")
    subprocess.run(["git", "add", "cfg.json"], cwd=repo_dir, capture_output=True)
    # Guard: no runner binaries installed — if a runner were invoked anyway,
    # the command would fail loudly (bash stubs below would not exist).

    result = _run_script(repo_dir)

    assert result.returncode == 0, result.stderr
    output = result.stdout.strip()
    assert "tests: n/a (syntax checkers only)" in output, f"unexpected:\n{output}"


def test_format_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Output always splits into exactly 4 pipe-separated named sections."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _init_repo(repo_dir)
    _write_config(repo_dir, ["rspec"])
    (repo_dir / "a.rb").write_text("module Helper\nend\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.rb"], cwd=repo_dir, capture_output=True)
    _install_fake_runner("rspec", repo_dir, monkeypatch, "1 examples, 0 failures\n")

    result = _run_script(repo_dir)

    assert result.returncode == 0, result.stderr
    output = result.stdout.strip()
    parts = output.split("|")
    assert len(parts) == 4, f"Expected 4 pipe-separated sections, got: {output}"
    prefixes = [part.strip().split(":")[0] for part in parts]
    assert prefixes == ["symbols", "breaks", "affects", "tests"], output