"""Intent tracking script tests (Story 06-02).

Tests for scripts/intent.py — deterministic intent management for session recovery.
Tests use tmp_path fixtures for isolation; no external systems required.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


# Make repo root importable for scripts
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def run_intent_script(
    args: list[str], pipeline_dir: Path
) -> tuple[int, str, str]:
    """Run intent.py script with given args and pipeline directory.
    
    Returns: (exit_code, stdout, stderr)
    """
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "intent.py"),
        "--pipeline-dir",
        str(pipeline_dir),
    ] + args
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_intent_start(tmp_path: Path) -> None:
    """Starting an intent writes entry with correct fields."""
    pipeline_dir = tmp_path / ".pipeline"
    pipeline_dir.mkdir()
    intent_file = pipeline_dir / "intent.json"
    intent_file.write_text('{"intents": []}')
    
    # Start an intent
    exit_code, stdout, stderr = run_intent_script(
        ["start", "06-01", "developer", "implement tests"],
        pipeline_dir,
    )
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Verify intent.json was updated
    data = json.loads(intent_file.read_text())
    assert "intents" in data
    assert len(data["intents"]) == 1
    
    intent = data["intents"][0]
    assert intent["story_id"] == "06-01"
    assert intent["agent"] == "developer"
    assert intent["step"] == "implement tests"
    assert intent["done"] is False
    assert "started_at" in intent
    assert "worktree" not in intent or intent.get("worktree") is None
    assert "branch" not in intent or intent.get("branch") is None


def test_intent_done(tmp_path: Path) -> None:
    """Marking done sets done: true on correct entry."""
    pipeline_dir = tmp_path / ".pipeline"
    pipeline_dir.mkdir()
    intent_file = pipeline_dir / "intent.json"
    
    # Start an intent
    run_intent_script(
        ["start", "06-01", "developer", "implement tests"],
        pipeline_dir,
    )
    
    # Mark it done
    exit_code, stdout, stderr = run_intent_script(
        ["done", "06-01"],
        pipeline_dir,
    )
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Verify intent.json was updated
    data = json.loads(intent_file.read_text())
    assert len(data["intents"]) == 1
    assert data["intents"][0]["done"] is True


def test_intent_show(tmp_path: Path) -> None:
    """Show returns all intents as JSON list."""
    pipeline_dir = tmp_path / ".pipeline"
    pipeline_dir.mkdir()
    intent_file = pipeline_dir / "intent.json"
    intent_file.write_text('{"intents": []}')
    
    # Start two intents
    run_intent_script(
        ["start", "06-01", "developer", "implement tests"],
        pipeline_dir,
    )
    run_intent_script(
        ["start", "06-02", "qa-manager", "review tests"],
        pipeline_dir,
    )
    
    # Show all intents
    exit_code, stdout, stderr = run_intent_script(
        ["show"],
        pipeline_dir,
    )
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Parse output as JSON
    intents = json.loads(stdout)
    assert isinstance(intents, list)
    assert len(intents) == 2
    assert intents[0]["story_id"] == "06-01"
    assert intents[1]["story_id"] == "06-02"


def test_intent_open(tmp_path: Path) -> None:
    """Open returns only entries with done: false."""
    pipeline_dir = tmp_path / ".pipeline"
    pipeline_dir.mkdir()
    intent_file = pipeline_dir / "intent.json"
    intent_file.write_text('{"intents": []}')
    
    # Start two intents
    run_intent_script(
        ["start", "06-01", "developer", "implement tests"],
        pipeline_dir,
    )
    run_intent_script(
        ["start", "06-02", "qa-manager", "review tests"],
        pipeline_dir,
    )
    
    # Mark first one done
    run_intent_script(
        ["done", "06-01"],
        pipeline_dir,
    )
    
    # Show only open intents
    exit_code, stdout, stderr = run_intent_script(
        ["open"],
        pipeline_dir,
    )
    
    assert exit_code == 0, f"Script failed: {stderr}"
    
    # Parse output as JSON
    intents = json.loads(stdout)
    assert isinstance(intents, list)
    assert len(intents) == 1
    assert intents[0]["story_id"] == "06-02"
    assert intents[0]["done"] is False


def test_intent_done_nonexistent(tmp_path: Path) -> None:
    """Marking done for non-existent story returns exit code 1."""
    pipeline_dir = tmp_path / ".pipeline"
    pipeline_dir.mkdir()
    intent_file = pipeline_dir / "intent.json"
    intent_file.write_text('{"intents": []}')
    
    # Try to mark a non-existent story as done
    exit_code, stdout, stderr = run_intent_script(
        ["done", "99-99"],
        pipeline_dir,
    )
    
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"


def test_intent_json_integrity(tmp_path: Path) -> None:
    """File is always valid JSON after any operation."""
    pipeline_dir = tmp_path / ".pipeline"
    pipeline_dir.mkdir()
    intent_file = pipeline_dir / "intent.json"
    intent_file.write_text('{"intents": []}')
    
    # Perform various operations
    run_intent_script(
        ["start", "06-01", "developer", "implement tests"],
        pipeline_dir,
    )
    run_intent_script(
        ["start", "06-02", "qa-manager", "review tests"],
        pipeline_dir,
    )
    run_intent_script(
        ["done", "06-01"],
        pipeline_dir,
    )
    run_intent_script(
        ["show"],
        pipeline_dir,
    )
    run_intent_script(
        ["open"],
        pipeline_dir,
    )
    
    # Verify file is still valid JSON
    content = intent_file.read_text()
    data = json.loads(content)
    assert "intents" in data
    assert isinstance(data["intents"], list)
