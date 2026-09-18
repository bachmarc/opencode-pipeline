"""Worktree setup script tests (Story 06-04).

Tests for scripts/worktree_setup.py — deterministic worktree/branch creation.
Tests use tmp_path fixtures with git init to create isolated test repos.
No external systems required.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


# Make repo root importable for scripts
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def run_worktree_script(
    args: list[str], repo_path: Path
) -> tuple[int, str, str]:
    """Run worktree_setup.py script with given args in a repo.
    
    Returns: (exit_code, stdout, stderr)
    """
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "worktree_setup.py"),
    ] + args
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(repo_path),
    )
    return result.returncode, result.stdout, result.stderr


def setup_test_repo(tmp_path: Path) -> Path:
    """Initialize a git repo with docs/features structure and a test story.
    
    Returns: path to the repo
    """
    repo = tmp_path / "test_repo"
    repo.mkdir()
    
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=str(repo),
        capture_output=True,
        check=True,
    )
    
    # Configure git user for commits
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(repo),
        capture_output=True,
        check=True,
    )
    
    # Create docs/features/test-feature/stories directory
    stories_dir = repo / "docs" / "features" / "test-feature" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a test story file
    story_file = stories_dir / "06-04-worktree-setup.md"
    story_file.write_text("# Test Story\n\nThis is a test story.\n")
    
    # Create main branch with initial commit
    (repo / "README.md").write_text("# Test Repo\n")
    subprocess.run(
        ["git", "add", "."],
        cwd=str(repo),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(repo),
        capture_output=True,
        check=True,
    )
    
    return repo


def test_script_exists() -> None:
    """Script exists and compiles."""
    script_path = SCRIPTS_DIR / "worktree_setup.py"
    assert script_path.exists(), f"Script not found at {script_path}"
    
    # Try to compile it
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(script_path)],
        capture_output=True,
    )
    assert result.returncode == 0, f"Script compilation failed: {result.stderr.decode()}"


def test_create_valid_story(tmp_path: Path) -> None:
    """Creates worktree for existing story."""
    repo = setup_test_repo(tmp_path)
    
    # Create worktree for valid story
    exit_code, stdout, stderr = run_worktree_script(
        ["create", "06-04"],
        repo,
    )
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Parse JSON output
    output = json.loads(stdout)
    assert "worktree" in output
    assert "branch" in output
    assert "story_file" in output
    
    # Verify worktree was created
    worktree_path = repo / output["worktree"]
    assert worktree_path.exists(), f"Worktree not created at {worktree_path}"
    
    # Verify branch name is correct
    assert output["branch"] == "feature/06-04-worktree-setup"
    
    # Verify story file path is correct
    assert "06-04-worktree-setup.md" in output["story_file"]


def test_create_nonexistent_story(tmp_path: Path) -> None:
    """Exit code 1 for missing story."""
    repo = setup_test_repo(tmp_path)
    
    # Try to create worktree for non-existent story
    exit_code, stdout, stderr = run_worktree_script(
        ["create", "99-99"],
        repo,
    )
    
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    
    # Output should still be JSON (error JSON)
    output = json.loads(stdout)
    assert "error" in output or "message" in output


def test_create_duplicate(tmp_path: Path) -> None:
    """Exit code 3 when worktree already exists."""
    repo = setup_test_repo(tmp_path)
    
    # Create worktree first time
    exit_code1, stdout1, stderr1 = run_worktree_script(
        ["create", "06-04"],
        repo,
    )
    assert exit_code1 == 0, f"First create failed: {stderr1}"
    
    # Try to create same worktree again
    exit_code2, stdout2, stderr2 = run_worktree_script(
        ["create", "06-04"],
        repo,
    )
    
    assert exit_code2 == 3, f"Expected exit code 3, got {exit_code2}"
    
    # Output should be JSON
    output = json.loads(stdout2)
    assert "error" in output or "message" in output


def test_list_worktrees(tmp_path: Path) -> None:
    """Lists created worktrees as JSON."""
    repo = setup_test_repo(tmp_path)
    
    # Create a worktree
    exit_code1, stdout1, stderr1 = run_worktree_script(
        ["create", "06-04"],
        repo,
    )
    assert exit_code1 == 0, f"Create failed: {stderr1}"
    
    # List worktrees
    exit_code, stdout, stderr = run_worktree_script(
        ["list"],
        repo,
    )
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Parse JSON output (should be array)
    output = json.loads(stdout)
    assert isinstance(output, list), f"Expected list, got {type(output)}"
    
    # Should contain at least one worktree
    assert len(output) >= 1, "No worktrees listed"
    
    # Check structure of first worktree
    wt = output[0]
    assert "path" in wt
    assert "branch" in wt
    assert "status" in wt


def test_output_is_json(tmp_path: Path) -> None:
    """Stdout is valid JSON for all subcommands."""
    repo = setup_test_repo(tmp_path)
    
    # Test create
    exit_code, stdout, stderr = run_worktree_script(
        ["create", "06-04"],
        repo,
    )
    assert exit_code == 0
    output = json.loads(stdout)  # Should not raise
    assert isinstance(output, dict)
    
    # Test list
    exit_code, stdout, stderr = run_worktree_script(
        ["list"],
        repo,
    )
    assert exit_code == 0
    output = json.loads(stdout)  # Should not raise
    assert isinstance(output, list)
