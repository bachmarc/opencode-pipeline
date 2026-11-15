"""Tests for booking_check.py script (Story 33-02).

Tests the booking check functionality: scanning story files for Done statuses
with SHAs and verifying those SHAs are ancestors of HEAD.

Uses subprocess to run the script with isolated test repos and mocked git commands.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCRIPT_PATH = SCRIPTS_DIR / "booking_check.py"


def run_booking_check_script(
    args: list[str], cwd: Path
) -> tuple[int, str, str]:
    """Run booking_check.py script with given args in specified directory.
    
    Returns: (exit_code, stdout, stderr)
    """
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
    ] + args
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def init_git_repo(repo_path: Path) -> None:
    """Initialize a git repository at the given path."""
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )


def create_commit(repo_path: Path, message: str = "test commit") -> str:
    """Create a commit and return its SHA."""
    # Create a dummy file
    dummy_file = repo_path / "dummy.txt"
    dummy_file.write_text(f"Commit: {message}\n")
    
    subprocess.run(
        ["git", "add", "dummy.txt"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )

    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=True,
    )

    # Extract SHA from output
    sha_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=True,
    )
    return sha_result.stdout.strip()


def test_script_exists() -> None:
    """Script exists and compiles without syntax errors."""
    assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"
    
    # Try to compile the script
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Script has syntax errors: {result.stderr}"


def test_no_violations_when_all_ancestors(tmp_path: Path) -> None:
    """All story-file SHAs are ancestors; run() returns empty list."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)
    
    # Create initial commit
    sha1 = create_commit(repo_path, "initial commit")
    
    # Create docs/features directory structure
    features_dir = repo_path / "docs" / "features"
    features_dir.mkdir(parents=True)
    
    # Create a story file with Done status containing the SHA (abbreviated)
    story_file = features_dir / "F-001-test" / "stories" / "01-01-test.md"
    story_file.parent.mkdir(parents=True)
    story_file.write_text(
        f"# Story 01-01\n"
        f"Status: Done (commit {sha1[:7]})\n"
    )
    
    # Run booking check
    exit_code, stdout, stderr = run_booking_check_script([], repo_path)
    
    # Should exit 0 (clean)
    assert exit_code == 0, f"Expected exit 0, got {exit_code}. stderr: {stderr}"
    
    # No violations should be reported
    assert "violation" not in stdout.lower(), f"Unexpected violations: {stdout}"


def test_violation_when_sha_not_ancestor(tmp_path: Path) -> None:
    """SHA not an ancestor; run() returns violation with story file and SHA."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)

    # Create initial commit on master (first commit on unnamed branch)
    create_commit(repo_path, "main commit")

    # Rename to main (so checkout works later)
    subprocess.run(
        ["git", "branch", "-m", "main"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    
    # Create a branch with a different commit
    subprocess.run(
        ["git", "checkout", "-b", "feature/test"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    sha_feature = create_commit(repo_path, "feature commit")
    
    # Switch back to main
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    
    # Create docs/features directory structure
    features_dir = repo_path / "docs" / "features"
    features_dir.mkdir(parents=True)
    
    # Create a story file with Done status containing the feature SHA
    # (which is NOT an ancestor of main)
    story_file = features_dir / "F-001-test" / "stories" / "01-01-test.md"
    story_file.parent.mkdir(parents=True)
    story_file.write_text(
        f"# Story 01-01\n"
        f"Status: Done (commit {sha_feature[:7]})\n"
    )
    
    # Run booking check
    exit_code, stdout, stderr = run_booking_check_script([], repo_path)
    
    # Should exit 1 (violation found)
    assert exit_code == 1, f"Expected exit 1, got {exit_code}. stderr: {stderr}"
    
    # Violation should be reported
    assert "violation" in stdout.lower() or sha_feature[:7] in stdout, \
        f"Expected violation in output: {stdout}"


def test_no_sha_in_done_status_ignored(tmp_path: Path) -> None:
    """Status: Done (no SHA) → not checked."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)

    # Create a commit
    create_commit(repo_path, "initial commit")

    # Create docs/features directory structure
    features_dir = repo_path / "docs" / "features"
    features_dir.mkdir(parents=True)

    # Create a story file with Done status but NO SHA
    story_file = features_dir / "F-001-test" / "stories" / "01-01-test.md"
    story_file.parent.mkdir(parents=True)
    story_file.write_text(
        "# Story 01-01\n"
        "Status: Done\n"
    )

    # Run booking check
    exit_code, _, stderr = run_booking_check_script([], repo_path)

    # Should exit 0 (clean) - no SHA to check
    assert exit_code == 0, f"Expected exit 0, got {exit_code}. stderr: {stderr}"


def test_cli_exit_0_clean(tmp_path: Path) -> None:
    """CLI exits 0 when no violations."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)

    # Create initial commit
    sha = create_commit(repo_path, "initial commit")

    # Create docs/features directory structure
    features_dir = repo_path / "docs" / "features"
    features_dir.mkdir(parents=True)

    # Create a story file with Done status containing the SHA
    story_file = features_dir / "F-001-test" / "stories" / "01-01-test.md"
    story_file.parent.mkdir(parents=True)
    story_file.write_text(
        f"# Story 01-01\n"
        f"Status: Done (commit {sha[:7]})\n"
    )

    # Run booking check
    exit_code, _, stderr = run_booking_check_script([], repo_path)

    # Should exit 0
    assert exit_code == 0, f"Expected exit 0, got {exit_code}. stderr: {stderr}"


def test_cli_exit_1_violation(tmp_path: Path) -> None:
    """CLI exits 1 when violation present."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)

    # Create initial commit on master (first commit on unnamed branch)
    create_commit(repo_path, "main commit")

    # Rename to main (so checkout works later)
    subprocess.run(
        ["git", "branch", "-m", "main"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )

    # Create a branch with a different commit
    subprocess.run(
        ["git", "checkout", "-b", "feature/test"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    sha_feature = create_commit(repo_path, "feature commit")

    # Switch back to main
    subprocess.run(
        ["git", "checkout", "main"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )

    # Create docs/features directory structure
    features_dir = repo_path / "docs" / "features"
    features_dir.mkdir(parents=True)

    # Create a story file with Done status containing the feature SHA
    story_file = features_dir / "F-001-test" / "stories" / "01-01-test.md"
    story_file.parent.mkdir(parents=True)
    story_file.write_text(
        f"# Story 01-01\n"
        f"Status: Done (commit {sha_feature[:7]})\n"
    )

    # Run booking check
    exit_code, _, stderr = run_booking_check_script([], repo_path)

    # Should exit 1
    assert exit_code == 1, f"Expected exit 1, got {exit_code}. stderr: {stderr}"
