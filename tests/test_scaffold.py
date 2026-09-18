"""Tests for scaffold_project.py — deterministic project scaffolding."""

import json
import subprocess
import sys
from pathlib import Path


def test_script_exists():
    """Script exists and compiles."""
    script_path = Path(__file__).parent.parent / "scripts" / "scaffold_project.py"
    assert script_path.exists(), f"Script not found at {script_path}"
    
    # Try to compile it
    with open(script_path) as f:
        code = f.read()
    compile(code, str(script_path), "exec")


def test_scaffold_creates_dirs(tmp_path):
    """All required directories exist after run."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    script_path = Path(__file__).parent.parent / "scripts" / "scaffold_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check all required directories exist
    required_dirs = [
        "docs",
        "docs/features",
        "tests",
        "tests/fakes",
        "src/core",
        "src/adapters",
        ".pipeline"
    ]
    
    for dir_name in required_dirs:
        dir_path = target / dir_name
        assert dir_path.exists() and dir_path.is_dir(), f"Directory {dir_name} not created"


def test_scaffold_copies_templates(tmp_path):
    """AGENTS.md in target matches source template."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    script_path = Path(__file__).parent.parent / "scripts" / "scaffold_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check AGENTS.md was copied
    target_agents = target / "AGENTS.md"
    assert target_agents.exists(), "AGENTS.md not copied to target"
    
    # Check it matches the source template
    source_agents = Path(__file__).parent.parent / "templates" / "AGENTS.md"
    assert source_agents.exists(), "Source AGENTS.md template not found"
    
    with open(source_agents, "rb") as f:
        source_content = f.read()
    with open(target_agents, "rb") as f:
        target_content = f.read()
    
    assert source_content == target_content, "AGENTS.md not byte-identical copy"


def test_scaffold_git_init(tmp_path):
    """`.git/` exists after scaffolding empty dir."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    script_path = Path(__file__).parent.parent / "scripts" / "scaffold_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check .git exists
    git_dir = target / ".git"
    assert git_dir.exists() and git_dir.is_dir(), ".git directory not created"


def test_scaffold_already_exists(tmp_path):
    """Exit code 2 when AGENTS.md already present."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    # Create AGENTS.md to simulate already scaffolded project
    (target / "AGENTS.md").write_text("# Already scaffolded\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "scaffold_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"


def test_scaffold_output_json(tmp_path):
    """Output is valid JSON with file list."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    script_path = Path(__file__).parent.parent / "scripts" / "scaffold_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Parse JSON output
    output = json.loads(result.stdout)
    
    # Check structure
    assert "created" in output, "JSON missing 'created' key"
    assert "target" in output, "JSON missing 'target' key"
    assert isinstance(output["created"], list), "'created' should be a list"
    assert len(output["created"]) > 0, "'created' list should not be empty"
    assert str(target) in output["target"], "'target' should contain the target path"
