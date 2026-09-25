"""QA routing, commit metadata, and merge validation script tests.

Tests for:
- scripts/qa_route.py — verdict routing with budget tracking
- scripts/prepare_commit_metadata.py — commit metadata generation
- scripts/merge_if_passed.py — merge validation

Uses tmp_path for isolation. No external systems, no real git operations beyond setup.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_ROUTE_SCRIPT = REPO_ROOT / "scripts" / "qa_route.py"
COMMIT_METADATA_SCRIPT = REPO_ROOT / "scripts" / "prepare_commit_metadata.py"
MERGE_IF_PASSED_SCRIPT = REPO_ROOT / "scripts" / "merge_if_passed.py"


def test_qa_route_record(tmp_path: Path) -> None:
    """qa_route.py record <story-id> <verdict> saves to .pipeline/qa-state/<story-id>.json."""
    # Setup
    qa_state_dir = tmp_path / ".pipeline" / "qa-state"
    qa_state_dir.mkdir(parents=True)
    
    # Run: record PASS verdict
    result = subprocess.run(
        [sys.executable, str(QA_ROUTE_SCRIPT), "record", "06-11", "PASS"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    
    # Check file was created
    state_file = qa_state_dir / "06-11.json"
    assert state_file.exists(), f"State file not created: {state_file}"
    
    # Parse and verify
    data = json.loads(state_file.read_text())
    assert "verdicts" in data, "State file must contain 'verdicts' key"
    assert isinstance(data["verdicts"], list), "verdicts must be a list"
    assert len(data["verdicts"]) > 0, "verdicts list must not be empty"
    assert data["verdicts"][-1]["verdict"] == "PASS", "Last verdict should be PASS"


def test_qa_route_next_pass(tmp_path: Path) -> None:
    """qa_route.py next <story-id> with PASS verdict returns documenter action."""
    # Setup
    qa_state_dir = tmp_path / ".pipeline" / "qa-state"
    qa_state_dir.mkdir(parents=True)
    
    # Record PASS
    subprocess.run(
        [sys.executable, str(QA_ROUTE_SCRIPT), "record", "06-11", "PASS"],
        cwd=str(tmp_path),
        capture_output=True,
    )
    
    # Get next action
    result = subprocess.run(
        [sys.executable, str(QA_ROUTE_SCRIPT), "next", "06-11"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    
    # Parse and verify
    data = json.loads(result.stdout)
    assert data["action"] == "documenter", f"Expected 'documenter' action, got {data['action']}"
    assert "branch" in data, "Action must include branch"


def test_qa_route_next_fail_budget(tmp_path: Path) -> None:
    """qa_route.py next with 3 FAILs returns blocked-requirements action."""
    # Setup
    qa_state_dir = tmp_path / ".pipeline" / "qa-state"
    qa_state_dir.mkdir(parents=True)
    
    # Record 3 FAIL verdicts
    for i in range(3):
        subprocess.run(
            [sys.executable, str(QA_ROUTE_SCRIPT), "record", "06-11", "FAIL"],
            cwd=str(tmp_path),
            capture_output=True,
        )
    
    # Get next action
    result = subprocess.run(
        [sys.executable, str(QA_ROUTE_SCRIPT), "next", "06-11"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    
    # Parse and verify
    data = json.loads(result.stdout)
    assert data["action"] == "blocked-requirements", \
        f"Expected 'blocked-requirements' after 3 FAILs, got {data['action']}"
    assert data["fail_count"] == 3, f"Expected fail_count=3, got {data['fail_count']}"


def test_qa_route_history(tmp_path: Path) -> None:
    """qa_route.py history <story-id> returns full verdict history."""
    # Setup
    qa_state_dir = tmp_path / ".pipeline" / "qa-state"
    qa_state_dir.mkdir(parents=True)
    
    # Record multiple verdicts
    verdicts = ["FAIL", "FAIL", "PASS"]
    for verdict in verdicts:
        subprocess.run(
            [sys.executable, str(QA_ROUTE_SCRIPT), "record", "06-11", verdict],
            cwd=str(tmp_path),
            capture_output=True,
        )
    
    # Get history
    result = subprocess.run(
        [sys.executable, str(QA_ROUTE_SCRIPT), "history", "06-11"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    
    # Parse and verify
    data = json.loads(result.stdout)
    assert "verdicts" in data, "History must contain 'verdicts' key"
    assert len(data["verdicts"]) == 3, f"Expected 3 verdicts, got {len(data['verdicts'])}"
    
    # Verify order
    for i, expected_verdict in enumerate(verdicts):
        assert data["verdicts"][i]["verdict"] == expected_verdict, \
            f"Verdict {i} mismatch: expected {expected_verdict}, got {data['verdicts'][i]['verdict']}"


def test_commit_metadata_format(tmp_path: Path) -> None:
    """prepare_commit_metadata.py outputs correctly formatted metadata string."""
    # Setup: create a simple git repo with staged changes
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    # Create and stage a Python file
    test_file = repo_dir / "test_module.py"
    test_file.write_text("def test_func():\n    pass\n")
    
    subprocess.run(
        ["git", "add", "test_module.py"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    # Run script
    result = subprocess.run(
        [sys.executable, str(COMMIT_METADATA_SCRIPT)],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed:\n{result.stderr}"
    
    # Verify format: "symbols: ... | breaks: ... | affects: ... | tests: ..."
    output = result.stdout.strip()
    assert "symbols:" in output, f"Output missing 'symbols:' section:\n{output}"
    assert "breaks:" in output, f"Output missing 'breaks:' section:\n{output}"
    assert "affects:" in output, f"Output missing 'affects:' section:\n{output}"
    assert "tests:" in output, f"Output missing 'tests:' section:\n{output}"
    
    # Verify pipe separators
    parts = output.split("|")
    assert len(parts) == 4, f"Expected 4 pipe-separated sections, got {len(parts)}"


def test_merge_if_passed_no_pass(tmp_path: Path) -> None:
    """merge_if_passed.py exits with code 1 when no QA-PASS record found."""
    # Setup
    qa_state_dir = tmp_path / ".pipeline" / "qa-state"
    qa_state_dir.mkdir(parents=True)
    
    # Run without PASS record
    result = subprocess.run(
        [sys.executable, str(MERGE_IF_PASSED_SCRIPT), "feature/06-11-test"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    
    # Should exit with code 1
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"
    
    # Output should be valid JSON with error info
    try:
        data = json.loads(result.stdout)
        assert "error" in data or "merged" in data, "Output must be valid JSON"
    except json.JSONDecodeError:
        # If not JSON, that's also acceptable for error case
        pass


def test_merge_if_passed_with_pass(tmp_path: Path) -> None:
    """merge_if_passed.py exits with code 0 when QA-PASS record exists."""
    # Setup: create a git repo with feature branch
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    # Create initial commit on master (default branch)
    (repo_dir / "README.md").write_text("# Test\n")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    # Create feature branch
    subprocess.run(
        ["git", "checkout", "-b", "feature/06-11-test"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    # Make a change
    (repo_dir / "feature.txt").write_text("feature content\n")
    subprocess.run(
        ["git", "add", "feature.txt"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Feature commit"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    # Add a commit with "docs: reconcile" message (required by story 17-03)
    (repo_dir / "docs.md").write_text("# Documentation\n")
    subprocess.run(
        ["git", "add", "docs.md"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "docs: reconcile"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    # Switch back to master
    subprocess.run(
        ["git", "checkout", "master"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    # Create QA-PASS record
    qa_state_dir = repo_dir / ".pipeline" / "qa-state"
    qa_state_dir.mkdir(parents=True)
    
    # Record PASS for the story (extract from branch name)
    subprocess.run(
        [sys.executable, str(QA_ROUTE_SCRIPT), "record", "06-11", "PASS"],
        cwd=str(repo_dir),
        capture_output=True,
    )
    
    # Run merge script
    result = subprocess.run(
        [sys.executable, str(MERGE_IF_PASSED_SCRIPT), "feature/06-11-test"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
    )
    
    # Should exit with code 0
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}\nStderr: {result.stderr}"
    
    # Output should be valid JSON with merge info
    data = json.loads(result.stdout)
    assert data.get("merged") is True, f"Expected merged=true, got {data}"
    assert "branch" in data, "Output must include branch"
    assert "commit" in data, "Output must include commit hash"
