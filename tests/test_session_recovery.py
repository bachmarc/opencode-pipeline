"""Session recovery script tests (Story 06-08).

Tests for scripts/session_recovery.py — comprehensive pipeline state collection.
Tests use tmp_path fixtures for isolated test repos; no external systems required.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Make repo root importable for scripts
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def run_session_recovery_script(
    args: list[str], cwd: Path
) -> tuple[int, str, str]:
    """Run session_recovery.py script with given args in specified directory.
    
    Returns: (exit_code, stdout, stderr)
    """
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "session_recovery.py"),
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


def test_script_exists() -> None:
    """Script exists and compiles without syntax errors."""
    script_path = SCRIPTS_DIR / "session_recovery.py"
    assert script_path.exists(), f"Script not found at {script_path}"
    
    # Try to compile the script
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Script has syntax errors: {result.stderr}"


def test_empty_state(tmp_path: Path) -> None:
    """Clean repo produces valid JSON with empty fields."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)
    
    # Create minimal .pipeline structure
    pipeline_dir = repo_path / ".pipeline"
    pipeline_dir.mkdir()
    (pipeline_dir / "intent.json").write_text('{"intents": []}')
    (pipeline_dir / "qa-state").mkdir()
    
    # Run session_recovery with no args
    exit_code, stdout, stderr = run_session_recovery_script([], repo_path)
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Parse output as JSON
    data = json.loads(stdout)
    
    # Verify structure
    assert "open_intents" in data
    assert "worktrees" in data
    assert "main_state" in data
    assert "qa_state" in data
    assert "feature_claims" in data
    
    # Verify empty fields
    assert isinstance(data["open_intents"], list)
    assert len(data["open_intents"]) == 0
    assert isinstance(data["worktrees"], list)
    assert len(data["worktrees"]) == 0
    assert isinstance(data["qa_state"], dict)
    assert len(data["qa_state"]) == 0
    assert isinstance(data["feature_claims"], list)
    assert len(data["feature_claims"]) == 0


def test_open_intent_detected(tmp_path: Path) -> None:
    """Open intent in .pipeline/intent.json appears in output."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)
    
    # Create .pipeline structure with an open intent
    pipeline_dir = repo_path / ".pipeline"
    pipeline_dir.mkdir()
    
    intent_data = {
        "intents": [
            {
                "story_id": "06-01",
                "agent": "developer",
                "step": "implement tests",
                "started_at": "2026-09-18T10:30:00Z",
                "done": False,
            }
        ]
    }
    (pipeline_dir / "intent.json").write_text(json.dumps(intent_data))
    (pipeline_dir / "qa-state").mkdir()
    
    # Run session_recovery
    exit_code, stdout, stderr = run_session_recovery_script([], repo_path)
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Parse output
    data = json.loads(stdout)
    
    # Verify open intent is detected
    assert len(data["open_intents"]) == 1
    assert data["open_intents"][0]["story_id"] == "06-01"
    assert data["open_intents"][0]["done"] is False


def test_worktree_detected(tmp_path: Path) -> None:
    """Existing worktree appears with correct branch/status."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)
    
    # Create .pipeline structure
    pipeline_dir = repo_path / ".pipeline"
    pipeline_dir.mkdir()
    (pipeline_dir / "intent.json").write_text('{"intents": []}')
    (pipeline_dir / "qa-state").mkdir()
    
    # Create a worktree directory with git repo
    worktree_path = repo_path / ".worktrees" / "06-01-test"
    init_git_repo(worktree_path)
    
    # Create a feature branch in the worktree
    subprocess.run(
        ["git", "checkout", "-b", "feature/06-01-test"],
        cwd=str(worktree_path),
        capture_output=True,
        check=True,
    )
    
    # Create a test file and commit it
    test_file = worktree_path / "test.txt"
    test_file.write_text("test content")
    subprocess.run(
        ["git", "add", "test.txt"],
        cwd=str(worktree_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(worktree_path),
        capture_output=True,
        check=True,
    )
    
    # Run session_recovery
    exit_code, stdout, stderr = run_session_recovery_script([], repo_path)
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Parse output
    data = json.loads(stdout)
    
    # Verify worktree is detected
    assert len(data["worktrees"]) == 1
    worktree = data["worktrees"][0]
    # Path may use forward or backslashes depending on OS
    assert "06-01-test" in worktree["path"]
    assert worktree["branch"] == "feature/06-01-test"
    assert isinstance(worktree["uncommitted_files"], list)
    assert isinstance(worktree["staged_files"], list)
    assert isinstance(worktree["merge_conflicts"], bool)
    assert isinstance(worktree["detached_head"], bool)


def test_check_flag_clean(tmp_path: Path) -> None:
    """--check returns 0 for clean state."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)
    
    # Create minimal .pipeline structure
    pipeline_dir = repo_path / ".pipeline"
    pipeline_dir.mkdir()
    (pipeline_dir / "intent.json").write_text('{"intents": []}')
    (pipeline_dir / "qa-state").mkdir()
    
    # Run with --check flag
    exit_code, _, _ = run_session_recovery_script(["--check"], repo_path)
    
    assert exit_code == 0, f"Expected exit code 0 for clean state, got {exit_code}"


def test_check_flag_dirty(tmp_path: Path) -> None:
    """--check returns 1 when open intents exist."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)
    
    # Create .pipeline structure with an open intent
    pipeline_dir = repo_path / ".pipeline"
    pipeline_dir.mkdir()
    
    intent_data = {
        "intents": [
            {
                "story_id": "06-01",
                "agent": "developer",
                "step": "implement tests",
                "started_at": "2026-09-18T10:30:00Z",
                "done": False,
            }
        ]
    }
    (pipeline_dir / "intent.json").write_text(json.dumps(intent_data))
    (pipeline_dir / "qa-state").mkdir()
    
    # Run with --check flag
    exit_code, _, _ = run_session_recovery_script(["--check"], repo_path)
    
    assert exit_code == 1, f"Expected exit code 1 for dirty state, got {exit_code}"


def test_output_is_valid_json(tmp_path: Path) -> None:
    """Stdout is parseable JSON."""
    repo_path = tmp_path / "test_repo"
    init_git_repo(repo_path)
    
    # Create minimal .pipeline structure
    pipeline_dir = repo_path / ".pipeline"
    pipeline_dir.mkdir()
    (pipeline_dir / "intent.json").write_text('{"intents": []}')
    (pipeline_dir / "qa-state").mkdir()
    
    # Run session_recovery
    exit_code, stdout, stderr = run_session_recovery_script([], repo_path)
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Verify stdout is valid JSON
    try:
        data = json.loads(stdout)
        assert isinstance(data, dict)
    except json.JSONDecodeError as e:
        pytest.fail(f"Output is not valid JSON: {e}\nOutput: {stdout}")
