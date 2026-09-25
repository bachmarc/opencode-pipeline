"""Tests for merge_if_passed.py script.

Tests the QA-PASS and documenter-reconcile checks before git merge.
Uses subprocess to run the script with mocked file system and git commands.
Verifies that documenter commits are scoped to branch-exclusive commits only
(commits on the feature branch but not on main).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "merge_if_passed.py"


def _create_fake_git_script(bin_dir: Path, name: str, output: str, exit_code: int = 0) -> None:
    """Create a fake git script that returns specified output and exit code."""
    script = bin_dir / name
    script.write_text(
        "#!/usr/bin/env bash\n"
        "cat <<'FAKE_GIT_EOF'\n"
        f"{output}"
        "FAKE_GIT_EOF\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    script.chmod(0o755)


def test_missing_qa_pass_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No qa-state file → exit 1, message contains 'no QA-PASS'."""
    # Setup: create pipeline dir but no qa-state file
    (tmp_path / ".pipeline" / "qa-state").mkdir(parents=True, exist_ok=True)
    
    # Create fake git binary
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _create_fake_git_script(bin_dir, "git", "")
    
    # Run script
    result = subprocess.run(
        ["python", str(SCRIPT_PATH), "feature/17-03-enforcement-bypass-fix"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", "")},
    )
    
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert "qa-pass" in output.get("error", "").lower()


def test_fail_verdict_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """qa-state with FAIL → exit 1, message contains 'no QA-PASS'."""
    # Setup: create qa-state file with FAIL verdict
    (tmp_path / ".pipeline" / "qa-state").mkdir(parents=True, exist_ok=True)
    qa_state_file = tmp_path / ".pipeline" / "qa-state" / "17-03.json"
    qa_state_file.write_text(
        json.dumps({
            "verdicts": [
                {"verdict": "FAIL", "timestamp": "2026-09-25T10:00:00Z"}
            ]
        })
    )
    
    # Create fake git binary
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _create_fake_git_script(bin_dir, "git", "")
    
    result = subprocess.run(
        ["python", str(SCRIPT_PATH), "feature/17-03-enforcement-bypass-fix"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", "")},
    )
    
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert "qa-pass" in output.get("error", "").lower()


def test_missing_documenter_commit_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """PASS present but no 'docs: reconcile' commit → exit 1, message contains 'documenter not run'."""
    # Setup: create qa-state file with PASS verdict
    (tmp_path / ".pipeline" / "qa-state").mkdir(parents=True, exist_ok=True)
    qa_state_file = tmp_path / ".pipeline" / "qa-state" / "17-03.json"
    qa_state_file.write_text(
        json.dumps({
            "verdicts": [
                {"verdict": "PASS", "timestamp": "2026-09-25T10:00:00Z"}
            ]
        })
    )
    
    # Create fake git binary that returns empty for log (no docs: reconcile commit)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _create_fake_git_script(bin_dir, "git", "", exit_code=1)
    
    result = subprocess.run(
        ["python", str(SCRIPT_PATH), "feature/17-03-enforcement-bypass-fix"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", "")},
    )
    
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert "documenter not run" in output.get("error", "").lower()


def test_both_checks_pass_calls_git_merge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """PASS + documenter commit present → git merge subprocess is called."""
    # Setup: create qa-state file with PASS verdict
    (tmp_path / ".pipeline" / "qa-state").mkdir(parents=True, exist_ok=True)
    qa_state_file = tmp_path / ".pipeline" / "qa-state" / "17-03.json"
    qa_state_file.write_text(
        json.dumps({
            "verdicts": [
                {"verdict": "PASS", "timestamp": "2026-09-25T10:00:00Z"}
            ]
        })
    )
    
    # Initialize a git repository in tmp_path
    subprocess.run(
        ["git", "init"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Configure git user for commits
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Create initial commit on master (default branch)
    (tmp_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Rename master to main
    subprocess.run(
        ["git", "branch", "-m", "master", "main"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/17-03-enforcement-bypass-fix"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Add a commit with "docs: reconcile" message
    (tmp_path / "test.txt").write_text("test content\n")
    subprocess.run(
        ["git", "add", "test.txt"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "docs: reconcile"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Switch back to main
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    result = subprocess.run(
        ["python", str(SCRIPT_PATH), "feature/17-03-enforcement-bypass-fix"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. stderr: {result.stderr}, stdout: {result.stdout}"
    output = json.loads(result.stdout)
    assert output.get("merged") is True
    assert "feature/17-03-enforcement-bypass-fix" in output.get("branch", "")


def test_documenter_commit_on_main_not_sufficient(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Documenter commit on main (ancestor) should NOT satisfy the check.
    
    When git log main..<branch> returns empty (no branch-exclusive commits),
    check_documenter_commit should return False even if docs: reconcile exists on main.
    """
    # Setup: create qa-state file with PASS verdict
    (tmp_path / ".pipeline" / "qa-state").mkdir(parents=True, exist_ok=True)
    qa_state_file = tmp_path / ".pipeline" / "qa-state" / "17-03.json"
    qa_state_file.write_text(
        json.dumps({
            "verdicts": [
                {"verdict": "PASS", "timestamp": "2026-09-25T10:00:00Z"}
            ]
        })
    )
    
    # Initialize a git repository in tmp_path
    subprocess.run(
        ["git", "init"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Configure git user for commits
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Create initial commit on master
    (tmp_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Rename master to main
    subprocess.run(
        ["git", "branch", "-m", "master", "main"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Create a commit with "docs: reconcile" on main
    (tmp_path / "docs.txt").write_text("docs content\n")
    subprocess.run(
        ["git", "add", "docs.txt"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "docs: reconcile"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Create feature branch (without any new commits)
    subprocess.run(
        ["git", "checkout", "-b", "feature/17-03-enforcement-bypass-fix"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Switch back to main
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    result = subprocess.run(
        ["python", str(SCRIPT_PATH), "feature/17-03-enforcement-bypass-fix"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    
    # Should fail because docs: reconcile is on main, not on branch-exclusive commits
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert "documenter not run" in output.get("error", "").lower()


def test_documenter_commit_on_branch_sufficient(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Documenter commit exclusively on branch should satisfy the check.
    
    When git log main..<branch> returns a commit with docs: reconcile,
    check_documenter_commit should return True.
    """
    # Setup: create qa-state file with PASS verdict
    (tmp_path / ".pipeline" / "qa-state").mkdir(parents=True, exist_ok=True)
    qa_state_file = tmp_path / ".pipeline" / "qa-state" / "17-03.json"
    qa_state_file.write_text(
        json.dumps({
            "verdicts": [
                {"verdict": "PASS", "timestamp": "2026-09-25T10:00:00Z"}
            ]
        })
    )
    
    # Initialize a git repository in tmp_path
    subprocess.run(
        ["git", "init"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Configure git user for commits
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Create initial commit on master
    (tmp_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Rename master to main
    subprocess.run(
        ["git", "branch", "-m", "master", "main"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/17-03-enforcement-bypass-fix"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Add a commit with "docs: reconcile" message on the branch
    (tmp_path / "test.txt").write_text("test content\n")
    subprocess.run(
        ["git", "add", "test.txt"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "docs: reconcile"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    # Switch back to main
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    
    result = subprocess.run(
        ["python", str(SCRIPT_PATH), "feature/17-03-enforcement-bypass-fix"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    
    # Should succeed because docs: reconcile is on branch-exclusive commits
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. stderr: {result.stderr}, stdout: {result.stdout}"
    output = json.loads(result.stdout)
    assert output.get("merged") is True
    assert "feature/17-03-enforcement-bypass-fix" in output.get("branch", "")
