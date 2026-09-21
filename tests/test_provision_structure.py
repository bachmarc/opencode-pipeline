"""Tests for provision_structure.py — deterministic structure provisioning."""

import json
import subprocess
import sys
from pathlib import Path


def test_script_exists():
    """Script exists and compiles."""
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    assert script_path.exists(), f"Script not found at {script_path}"
    
    # Try to compile it
    with open(script_path) as f:
        code = f.read()
    compile(code, str(script_path), "exec")


def test_creates_missing_pipeline_dir(tmp_path):
    """Temp dir without .pipeline/ → .pipeline/ created, in 'created' list."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    # Create minimal analysis JSON
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {
            "present": [],
            "missing": [".pipeline"]
        }
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check .pipeline/ was created
    pipeline_dir = target / ".pipeline"
    assert pipeline_dir.exists() and pipeline_dir.is_dir(), ".pipeline/ not created"
    
    # Check output JSON
    output = json.loads(result.stdout)
    assert ".pipeline" in output["created"], ".pipeline not in 'created' list"


def test_skips_existing_dirs(tmp_path):
    """Temp dir with src/core/ already → src/core in 'already_existed' list."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    # Create src/core directory
    src_core = target / "src" / "core"
    src_core.mkdir(parents=True)
    
    # Create minimal analysis JSON
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {
            "present": ["src/core"],
            "missing": []
        }
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check output JSON
    output = json.loads(result.stdout)
    assert "src/core" in output["already_existed"], "src/core not in 'already_existed' list"


def test_creates_qa_config_python(tmp_path):
    """Python analysis → qa_config.json contains ["pytest"]."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {"present": [], "missing": []}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check qa_config.json
    qa_config_path = target / "qa_config.json"
    assert qa_config_path.exists(), "qa_config.json not created"
    
    qa_config = json.loads(qa_config_path.read_text())
    assert "checkers" in qa_config, "qa_config.json missing 'checkers' key"
    assert "pytest" in qa_config["checkers"], "pytest not in checkers for Python stack"


def test_creates_qa_config_javascript(tmp_path):
    """JavaScript analysis → qa_config.json contains ["jest"]."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    analysis = {
        "project_name": "test-project",
        "stack": "javascript",
        "structure": {"present": [], "missing": []}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check qa_config.json
    qa_config_path = target / "qa_config.json"
    assert qa_config_path.exists(), "qa_config.json not created"
    
    qa_config = json.loads(qa_config_path.read_text())
    assert "jest" in qa_config["checkers"], "jest not in checkers for JavaScript stack"


def test_creates_qa_config_ruby(tmp_path):
    """Ruby analysis → qa_config.json contains ["rspec"]."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    analysis = {
        "project_name": "test-project",
        "stack": "ruby",
        "structure": {"present": [], "missing": []}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check qa_config.json
    qa_config_path = target / "qa_config.json"
    assert qa_config_path.exists(), "qa_config.json not created"
    
    qa_config = json.loads(qa_config_path.read_text())
    assert "rspec" in qa_config["checkers"], "rspec not in checkers for Ruby stack"


def test_never_overwrites_existing(tmp_path):
    """Temp dir with existing STORIES.md → content unchanged after provisioning."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    # Create existing STORIES.md with custom content
    stories_path = target / "STORIES.md"
    original_content = "# My Custom Stories\n\nThis is my content.\n"
    stories_path.write_text(original_content)
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {"present": [], "missing": []}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check content is unchanged
    assert stories_path.read_text() == original_content, "STORIES.md was overwritten"


def test_gitignore_merge_appends(tmp_path):
    """Temp dir with existing .gitignore containing "*.pyc" → after provisioning, still contains "*.pyc" plus pipeline entries."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    # Create existing .gitignore
    gitignore_path = target / ".gitignore"
    gitignore_path.write_text("*.pyc\n")
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {"present": [], "missing": []}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check content
    gitignore_content = gitignore_path.read_text()
    assert "*.pyc" in gitignore_content, "Original *.pyc entry was removed"
    assert ".pipeline/" in gitignore_content, ".pipeline/ not added to .gitignore"
    assert ".worktrees/" in gitignore_content, ".worktrees/ not added to .gitignore"


def test_gitignore_no_duplicates(tmp_path):
    """Temp dir with .gitignore already containing ".pipeline/" → no duplicate ".pipeline/" entry after provisioning."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    # Create existing .gitignore with .pipeline/ already present
    gitignore_path = target / ".gitignore"
    gitignore_path.write_text(".pipeline/\n*.log\n")
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {"present": [], "missing": []}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check no duplicates
    gitignore_content = gitignore_path.read_text()
    count = gitignore_content.count(".pipeline/")
    assert count == 1, f"Found {count} occurrences of '.pipeline/', expected 1"


def test_copies_story_template(tmp_path):
    """After provisioning → docs/features/_story_template.md exists."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {"present": [], "missing": ["docs/features"]}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check template was copied
    story_template = target / "docs" / "features" / "_story_template.md"
    assert story_template.exists(), "_story_template.md not copied"
    
    # Check it matches the source template
    source_template = Path(__file__).parent.parent / "docs" / "features" / "_story_template.md"
    assert source_template.exists(), "Source _story_template.md not found"
    
    assert story_template.read_text() == source_template.read_text(), "Template content doesn't match"


def test_copies_feature_template(tmp_path):
    """After provisioning → docs/features/_feature_template.md exists."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {"present": [], "missing": ["docs/features"]}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check template was copied
    feature_template = target / "docs" / "features" / "_feature_template.md"
    assert feature_template.exists(), "_feature_template.md not copied"
    
    # Check it matches the source template
    source_template = Path(__file__).parent.parent / "docs" / "features" / "_feature_template.md"
    assert source_template.exists(), "Source _feature_template.md not found"
    
    assert feature_template.read_text() == source_template.read_text(), "Template content doesn't match"


def test_nonexistent_path(tmp_path):
    """Exit code 1 for nonexistent path."""
    nonexistent = tmp_path / "does_not_exist"
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {"present": [], "missing": []}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(nonexistent), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"


def test_creates_intent_json(tmp_path):
    """After provisioning → .pipeline/intent.json exists with project name."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    analysis = {
        "project_name": "my-test-project",
        "stack": "python",
        "structure": {"present": [], "missing": [".pipeline"]}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check intent.json
    intent_path = target / ".pipeline" / "intent.json"
    assert intent_path.exists(), ".pipeline/intent.json not created"
    
    intent = json.loads(intent_path.read_text())
    assert intent["project"] == "my-test-project", "Project name not set correctly"
    assert intent["created"] is True, "created flag not set"


def test_creates_features_and_stories_md(tmp_path):
    """After provisioning → FEATURES.md and STORIES.md exist with starter content."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {"present": [], "missing": []}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check FEATURES.md
    features_path = target / "FEATURES.md"
    assert features_path.exists(), "FEATURES.md not created"
    assert "# Features" in features_path.read_text(), "FEATURES.md missing header"
    
    # Check STORIES.md
    stories_path = target / "STORIES.md"
    assert stories_path.exists(), "STORIES.md not created"
    assert "# Stories" in stories_path.read_text(), "STORIES.md missing header"


def test_output_json_structure(tmp_path):
    """Output JSON has correct structure with 'created', 'already_existed', 'gitignore_entries_added'."""
    target = tmp_path / "test_project"
    target.mkdir()
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "structure": {"present": [], "missing": [".pipeline"]}
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "provision_structure.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target), str(analysis_file)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Parse output JSON
    output = json.loads(result.stdout)
    
    # Check structure
    assert "created" in output, "JSON missing 'created' key"
    assert "already_existed" in output, "JSON missing 'already_existed' key"
    assert "gitignore_entries_added" in output, "JSON missing 'gitignore_entries_added' key"
    
    assert isinstance(output["created"], list), "'created' should be a list"
    assert isinstance(output["already_existed"], list), "'already_existed' should be a list"
    assert isinstance(output["gitignore_entries_added"], list), "'gitignore_entries_added' should be a list"
