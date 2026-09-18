"""Feature claim/release script tests (Story 06-09).

Tests for deterministic feature claiming with multi-user isolation.
Uses tmp_path with git init for isolated test repos.

Stdlib only — no external systems, deterministic.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "feature_claim.py"


def init_test_repo(tmp_path: Path) -> Path:
    """Initialize a test git repo with feature.md files.
    
    Returns the repo root path.
    """
    repo = tmp_path / "test_repo"
    repo.mkdir()
    
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    
    # Configure git user for commits
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    
    # Create features directory structure
    features_dir = repo / "docs" / "features"
    
    # Feature 1: unclaimed
    feature1_dir = features_dir / "feature-one"
    feature1_dir.mkdir(parents=True, exist_ok=True)
    feature1_md = feature1_dir / "feature.md"
    feature1_md.write_text(
        """---
id: F-001
title: Feature One
status: planned
owner: ""
---

## Vision

Test feature one vision.

## Context

Test feature one.
"""
    )
    
    # Feature 2: unclaimed
    feature2_dir = features_dir / "feature-two"
    feature2_dir.mkdir(parents=True, exist_ok=True)
    feature2_md = feature2_dir / "feature.md"
    feature2_md.write_text(
        """---
id: F-002
title: Feature Two
status: planned
owner: ""
---

## Vision

Test feature two vision.

## Context

Test feature two.
"""
    )
    
    # Feature 3: already claimed (old)
    feature3_dir = features_dir / "feature-three"
    feature3_dir.mkdir(parents=True, exist_ok=True)
    feature3_md = feature3_dir / "feature.md"
    old_timestamp = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
    feature3_md.write_text(
        f"""---
id: F-003
title: Feature Three
status: claimed
owner: "olduser@oldhost"
claimed_at: "{old_timestamp}"
---

## Vision

Test feature three vision (old claim).

## Context

Test feature three (old claim).
"""
    )
    
    # Initial commit
    subprocess.run(
        ["git", "add", "."],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    
    return repo


def run_script(
    repo: Path,
    args: list[str],
    local_only: bool = True,
) -> tuple[int, str, str]:
    """Run the feature_claim.py script and return (exit_code, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPT_PATH), "--repo-dir", str(repo)]
    if local_only:
        cmd.append("--local-only")
    cmd.extend(args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    
    return result.returncode, result.stdout, result.stderr


def test_script_exists() -> None:
    """Script exists and is executable."""
    assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"
    
    # Try to compile it
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(SCRIPT_PATH)],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, f"Script has syntax errors: {result.stderr.decode()}"


def test_claim_unclaimed(tmp_path: Path) -> None:
    """Claim succeeds for unclaimed feature, updates feature.md."""
    repo = init_test_repo(tmp_path)
    
    exit_code, stdout, stderr = run_script(repo, ["claim", "feature-one"])
    
    assert exit_code == 0, f"Claim failed: {stderr}"
    
    # Parse output JSON
    output = json.loads(stdout)
    assert output["claimed"] is True
    assert output["feature"] == "feature-one"
    assert "owner" in output
    assert "@" in output["owner"]  # Should be user@host format
    
    # Check that feature.md was updated
    feature_md = repo / "docs" / "features" / "feature-one" / "feature.md"
    content = feature_md.read_text()
    assert "status: claimed" in content
    assert f"owner: \"{output['owner']}\"" in content
    assert "claimed_at:" in content


def test_claim_already_claimed(tmp_path: Path) -> None:
    """Claim fails (exit 1) when feature already claimed by someone else."""
    repo = init_test_repo(tmp_path)
    
    # First claim should succeed
    exit_code1, _, _ = run_script(repo, ["claim", "feature-one"])
    assert exit_code1 == 0
    
    # Second claim should fail with exit code 1
    exit_code2, stdout2, stderr2 = run_script(repo, ["claim", "feature-one"])
    assert exit_code2 == 1, f"Expected exit code 1, got {exit_code2}: {stderr2}"
    
    # Output should be error JSON
    output = json.loads(stdout2)
    assert output.get("claimed") is False or "error" in output


def test_release(tmp_path: Path) -> None:
    """Release resets status and clears owner."""
    repo = init_test_repo(tmp_path)
    
    # First claim
    exit_code1, _, _ = run_script(repo, ["claim", "feature-one"])
    assert exit_code1 == 0
    
    # Then release
    exit_code2, stdout2, stderr2 = run_script(repo, ["release", "feature-one"])
    assert exit_code2 == 0, f"Release failed: {stderr2}"
    
    # Parse output JSON
    output = json.loads(stdout2)
    assert output["released"] is True
    assert output["feature"] == "feature-one"
    
    # Check that feature.md was updated
    feature_md = repo / "docs" / "features" / "feature-one" / "feature.md"
    content = feature_md.read_text()
    assert "status: planned" in content
    assert 'owner: ""' in content


def test_status_output(tmp_path: Path) -> None:
    """Status outputs valid JSON array with all features."""
    repo = init_test_repo(tmp_path)
    
    # Claim one feature
    run_script(repo, ["claim", "feature-one"])
    
    # Get status
    exit_code, stdout, stderr = run_script(repo, ["status"])
    assert exit_code == 0, f"Status failed: {stderr}"
    
    # Parse output JSON
    output = json.loads(stdout)
    assert isinstance(output, list), "Status output should be a JSON array"
    assert len(output) >= 2, "Should have at least 2 features"
    
    # Check structure
    for feature in output:
        assert "feature" in feature or "id" in feature
        assert "status" in feature
        assert "owner" in feature


def test_check_stale(tmp_path: Path) -> None:
    """Check-stale correctly identifies old claims."""
    repo = init_test_repo(tmp_path)
    
    # feature-three was created with an old timestamp (48 hours ago)
    # Check for claims older than 24 hours
    exit_code, stdout, stderr = run_script(repo, ["check-stale", "--hours", "24"])
    assert exit_code == 0, f"Check-stale failed: {stderr}"
    
    # Parse output JSON
    output = json.loads(stdout)
    assert isinstance(output, list), "Check-stale output should be a JSON array"
    
    # Should find feature-three as stale
    stale_features = [f for f in output if f.get("feature") == "feature-three"]
    assert len(stale_features) > 0, "Should find feature-three as stale"


def test_claim_nonexistent(tmp_path: Path) -> None:
    """Claim fails (exit 2) for unknown feature."""
    repo = init_test_repo(tmp_path)
    
    exit_code, stdout, stderr = run_script(repo, ["claim", "nonexistent-feature"])
    assert exit_code == 2, f"Expected exit code 2, got {exit_code}: {stderr}"
    
    # Output should be error JSON
    output = json.loads(stdout)
    assert "error" in output or output.get("claimed") is False
