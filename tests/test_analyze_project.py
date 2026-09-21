"""Tests for analyze_project.py — deterministic project analysis."""

import json
import subprocess
import sys
from pathlib import Path


def test_script_exists():
    """Script exists and compiles."""
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    assert script_path.exists(), f"Script not found at {script_path}"
    
    # Try to compile it
    with open(script_path) as f:
        code = f.read()
    compile(code, str(script_path), "exec")


def test_analyze_python_project(tmp_path):
    """Temp dir with requirements.txt → stack includes 'python'."""
    target = tmp_path / "python_project"
    target.mkdir()
    (target / "requirements.txt").write_text("requests==2.28.0\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "python" in output["stack"], f"Expected 'python' in stack, got {output['stack']}"


def test_analyze_js_project(tmp_path):
    """Temp dir with package.json → stack includes 'javascript'."""
    target = tmp_path / "js_project"
    target.mkdir()
    (target / "package.json").write_text('{"name": "test"}\n')
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "javascript" in output["stack"], f"Expected 'javascript' in stack, got {output['stack']}"


def test_analyze_ruby_project(tmp_path):
    """Temp dir with Gemfile → stack includes 'ruby'."""
    target = tmp_path / "ruby_project"
    target.mkdir()
    (target / "Gemfile").write_text("gem 'rails'\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "ruby" in output["stack"], f"Expected 'ruby' in stack, got {output['stack']}"


def test_analyze_java_project_pom(tmp_path):
    """Temp dir with pom.xml → stack includes 'java'."""
    target = tmp_path / "java_project"
    target.mkdir()
    (target / "pom.xml").write_text("<project></project>\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "java" in output["stack"], f"Expected 'java' in stack, got {output['stack']}"


def test_analyze_java_project_gradle(tmp_path):
    """Temp dir with build.gradle → stack includes 'java'."""
    target = tmp_path / "java_gradle_project"
    target.mkdir()
    (target / "build.gradle").write_text("plugins {}\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "java" in output["stack"], f"Expected 'java' in stack, got {output['stack']}"


def test_analyze_mixed_project(tmp_path):
    """Temp dir with requirements.txt + package.json → stack is 'mixed'."""
    target = tmp_path / "mixed_project"
    target.mkdir()
    (target / "requirements.txt").write_text("requests==2.28.0\n")
    (target / "package.json").write_text('{"name": "test"}\n')
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["stack"] == "mixed", f"Expected 'mixed', got {output['stack']}"


def test_analyze_unknown_stack(tmp_path):
    """Empty temp dir → stack is 'unknown'."""
    target = tmp_path / "unknown_project"
    target.mkdir()
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["stack"] == "unknown", f"Expected 'unknown', got {output['stack']}"


def test_detect_agents_md(tmp_path):
    """Temp dir with AGENTS.md → agent_file.type == 'agents.md'."""
    target = tmp_path / "agents_project"
    target.mkdir()
    agents_content = "# AGENTS.md\n\nTest content\n"
    (target / "AGENTS.md").write_text(agents_content)
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["agent_file"]["type"] == "agents.md", f"Expected 'agents.md', got {output['agent_file']['type']}"
    assert output["agent_file"]["content"] == agents_content, "Content mismatch"


def test_detect_claude_md(tmp_path):
    """Temp dir with CLAUDE.md → agent_file.type == 'claude.md'."""
    target = tmp_path / "claude_project"
    target.mkdir()
    claude_content = "# CLAUDE.md\n\nTest content\n"
    (target / "CLAUDE.md").write_text(claude_content)
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["agent_file"]["type"] == "claude.md", f"Expected 'claude.md', got {output['agent_file']['type']}"
    assert output["agent_file"]["content"] == claude_content, "Content mismatch"


def test_detect_no_agent_file(tmp_path):
    """Empty temp dir → agent_file.type == 'none'."""
    target = tmp_path / "no_agent_project"
    target.mkdir()
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["agent_file"]["type"] == "none", f"Expected 'none', got {output['agent_file']['type']}"
    assert output["agent_file"]["content"] is None, "Content should be None"


def test_missing_directories(tmp_path):
    """Temp dir without src/core/ → 'src/core' in missing list."""
    target = tmp_path / "incomplete_project"
    target.mkdir()
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "src/core" in output["missing"], f"Expected 'src/core' in missing, got {output['missing']}"


def test_present_directories(tmp_path):
    """Temp dir with src/core/ → 'src/core' not in missing list."""
    target = tmp_path / "complete_project"
    target.mkdir()
    (target / "src" / "core").mkdir(parents=True)
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "src/core" not in output["missing"], f"'src/core' should not be in missing"


def test_nonexistent_path():
    """Nonexistent path → exit code 1."""
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "/nonexistent/path/12345"],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"


def test_not_a_directory(tmp_path):
    """File path instead of directory → exit code 2."""
    target = tmp_path / "file.txt"
    target.write_text("test")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"


def test_output_json_structure(tmp_path):
    """Output contains all required keys."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    
    # Check required keys
    required_keys = [
        "project_name",
        "stack",
        "agent_file",
        "structure",
        "git",
        "missing",
        "existing_pipeline_files"
    ]
    
    for key in required_keys:
        assert key in output, f"Missing required key: {key}"


def test_git_state_extraction(tmp_path):
    """Git state is extracted correctly."""
    target = tmp_path / "git_project"
    target.mkdir()
    
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=target,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=target,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=target,
        capture_output=True,
        check=True
    )
    
    # Create initial commit
    (target / "README.md").write_text("# Test\n")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=target,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=target,
        capture_output=True,
        check=True
    )
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    
    # Check git state structure
    assert "git" in output
    assert "current_branch" in output["git"]
    assert "branches" in output["git"]
    assert "has_main" in output["git"]
    assert "has_master" in output["git"]
    assert "remotes" in output["git"]


def test_existing_pipeline_files(tmp_path):
    """Existing pipeline files are detected."""
    target = tmp_path / "pipeline_project"
    target.mkdir()
    
    # Create some pipeline files
    (target / "STORIES.md").write_text("# Stories\n")
    (target / "FEATURES.md").write_text("# Features\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    
    # Check that existing files are detected
    assert "STORIES.md" in output["existing_pipeline_files"]
    assert "FEATURES.md" in output["existing_pipeline_files"]
