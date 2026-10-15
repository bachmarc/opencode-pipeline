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


# Tests for test_command, qa_checker, and deploy_hints detection

def test_detect_test_command_python(tmp_path):
    """Project with requirements.txt → test_command='pytest', qa_checkers=['pytest', 'mypy', 'ruff']."""
    target = tmp_path / "python_project"
    target.mkdir()
    (target / "requirements.txt").write_text("pytest==7.0.0\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["test_command"] == "pytest", f"Expected 'pytest', got {output['test_command']}"
    assert output["qa_checkers"] == ["pytest", "mypy", "ruff"], f"Expected ['pytest', 'mypy', 'ruff'], got {output['qa_checkers']}"


def test_detect_test_command_ruby(tmp_path):
    """Project with Gemfile → test_command='bundle exec rspec', qa_checkers=['rspec', 'rubocop']."""
    target = tmp_path / "ruby_project"
    target.mkdir()
    (target / "Gemfile").write_text("gem 'rspec'\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["test_command"] == "bundle exec rspec", f"Expected 'bundle exec rspec', got {output['test_command']}"
    assert output["qa_checkers"] == ["rspec", "rubocop"], f"Expected ['rspec', 'rubocop'], got {output['qa_checkers']}"


def test_detect_test_command_node(tmp_path):
    """Project with package.json (plain JS) → test_command='npm test', qa_checkers=['jest', 'eslint', 'prettier', 'npm-audit']."""
    target = tmp_path / "node_project"
    target.mkdir()
    (target / "package.json").write_text('{"name": "test", "scripts": {"test": "jest"}}\n')
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["test_command"] == "npm test", f"Expected 'npm test', got {output['test_command']}"
    assert output["qa_checkers"] == ["jest", "eslint", "prettier", "npm-audit"], f"Expected JS checkers, got {output['qa_checkers']}"


def test_detect_test_command_maven(tmp_path):
    """Project with pom.xml → test_command='mvn test', qa_checkers=['maven', 'checkstyle']."""
    target = tmp_path / "maven_project"
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
    assert output["test_command"] == "mvn test", f"Expected 'mvn test', got {output['test_command']}"
    assert output["qa_checkers"] == ["maven", "checkstyle"], f"Expected ['maven', 'checkstyle'], got {output['qa_checkers']}"


def test_detect_test_command_gradle(tmp_path):
    """Project with build.gradle → test_command='./gradlew test', qa_checkers=['gradle', 'checkstyle']."""
    target = tmp_path / "gradle_project"
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
    assert output["test_command"] == "./gradlew test", f"Expected './gradlew test', got {output['test_command']}"
    assert output["qa_checkers"] == ["gradle", "checkstyle"], f"Expected ['gradle', 'checkstyle'], got {output['qa_checkers']}"


def test_detect_test_command_unknown(tmp_path):
    """Empty project → test_command='unknown', qa_checkers=['pytest'], qa_bootstrap_needed=true."""
    target = tmp_path / "empty_project"
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
    assert output["test_command"] == "unknown", f"Expected 'unknown', got {output['test_command']}"
    assert output["qa_checkers"] == ["pytest"], f"Expected ['pytest'], got {output['qa_checkers']}"
    assert output["qa_bootstrap_needed"] == True, f"Expected qa_bootstrap_needed=True for unknown stack"


def test_deploy_hints_github_actions(tmp_path):
    """Project with .github/workflows/ → 'github-actions' in hints."""
    target = tmp_path / "github_project"
    target.mkdir()
    (target / ".github" / "workflows").mkdir(parents=True)
    (target / ".github" / "workflows" / "ci.yml").write_text("name: CI\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "github-actions" in output["deploy_hints"], f"Expected 'github-actions' in {output['deploy_hints']}"


def test_deploy_hints_dockerfile(tmp_path):
    """Project with Dockerfile → 'dockerfile' in hints."""
    target = tmp_path / "docker_project"
    target.mkdir()
    (target / "Dockerfile").write_text("FROM python:3.9\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "dockerfile" in output["deploy_hints"], f"Expected 'dockerfile' in {output['deploy_hints']}"


def test_deploy_hints_makefile_target(tmp_path):
    """Project with Makefile containing deploy: → 'makefile-deploy-target' in hints."""
    target = tmp_path / "makefile_project"
    target.mkdir()
    (target / "Makefile").write_text("build:\n\techo building\n\ndeploy:\n\techo deploying\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "makefile-deploy-target" in output["deploy_hints"], f"Expected 'makefile-deploy-target' in {output['deploy_hints']}"


def test_deploy_hints_heroku(tmp_path):
    """Project with Procfile → 'heroku' in hints."""
    target = tmp_path / "heroku_project"
    target.mkdir()
    (target / "Procfile").write_text("web: python app.py\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "heroku" in output["deploy_hints"], f"Expected 'heroku' in {output['deploy_hints']}"


def test_deploy_hints_scp_script(tmp_path):
    """Project with deploy.sh → 'scp-script' in hints."""
    target = tmp_path / "scp_project"
    target.mkdir()
    (target / "deploy.sh").write_text("#!/bin/bash\nscp -r . user@host:/app\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "scp-script" in output["deploy_hints"], f"Expected 'scp-script' in {output['deploy_hints']}"


def test_deploy_hints_multiple(tmp_path):
    """Project with Dockerfile and .github/workflows/ → both hints present."""
    target = tmp_path / "multi_deploy_project"
    target.mkdir()
    (target / "Dockerfile").write_text("FROM python:3.9\n")
    (target / ".github" / "workflows").mkdir(parents=True)
    (target / ".github" / "workflows" / "ci.yml").write_text("name: CI\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "dockerfile" in output["deploy_hints"], f"Expected 'dockerfile' in {output['deploy_hints']}"
    assert "github-actions" in output["deploy_hints"], f"Expected 'github-actions' in {output['deploy_hints']}"


def test_deploy_hints_unknown(tmp_path):
    """Project with no deploy signals → deploy_hints=['unknown']."""
    target = tmp_path / "no_deploy_project"
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
    assert output["deploy_hints"] == ["unknown"], f"Expected ['unknown'], got {output['deploy_hints']}"


def test_existing_fields_unchanged(tmp_path):
    """Existing output fields still present after extension."""
    target = tmp_path / "existing_fields_project"
    target.mkdir()
    (target / "requirements.txt").write_text("pytest==7.0.0\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    
    # Check that all original fields are still present
    required_keys = [
        "project_name",
        "stack",
        "agent_file",
        "structure",
        "git",
        "missing",
        "existing_pipeline_files",
        "test_command",
        "qa_checkers",
        "qa_bootstrap_needed",
        "deploy_hints"
    ]
    
    for key in required_keys:
        assert key in output, f"Missing required key: {key}"


# New tests for Story 27-05: full qa_checkers list per stack

def test_typescript_project_gets_tsc_checker(tmp_path):
    """Project with package.json + tsconfig.json → 'tsc' in qa_checkers."""
    target = tmp_path / "ts_project"
    target.mkdir()
    (target / "package.json").write_text('{"name": "test"}\n')
    (target / "tsconfig.json").write_text('{"compilerOptions": {"target": "es2020"}}\n')
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "tsc" in output["qa_checkers"], f"Expected 'tsc' in {output['qa_checkers']}"
    assert output["qa_checkers"] == ["jest", "eslint", "tsc", "prettier", "npm-audit"], \
        f"Expected full TS checker set, got {output['qa_checkers']}"


def test_typescript_project_with_ts_files(tmp_path):
    """Project with package.json + .ts file in root → 'tsc' in qa_checkers."""
    target = tmp_path / "ts_project2"
    target.mkdir()
    (target / "package.json").write_text('{"name": "test"}\n')
    (target / "index.ts").write_text("console.log('test');\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "tsc" in output["qa_checkers"], f"Expected 'tsc' in {output['qa_checkers']}"


def test_typescript_project_with_src_ts_files(tmp_path):
    """Project with package.json + .ts file in src/ → 'tsc' in qa_checkers."""
    target = tmp_path / "ts_project3"
    target.mkdir()
    (target / "package.json").write_text('{"name": "test"}\n')
    (target / "src").mkdir()
    (target / "src" / "index.ts").write_text("console.log('test');\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "tsc" in output["qa_checkers"], f"Expected 'tsc' in {output['qa_checkers']}"


def test_javascript_project_no_tsc(tmp_path):
    """Project with only package.json (no tsconfig, no .ts files) → no 'tsc'."""
    target = tmp_path / "js_only_project"
    target.mkdir()
    (target / "package.json").write_text('{"name": "test"}\n')
    (target / "index.js").write_text("console.log('test');\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "tsc" not in output["qa_checkers"], f"'tsc' should not be in {output['qa_checkers']}"
    assert output["qa_checkers"] == ["jest", "eslint", "prettier", "npm-audit"], \
        f"Expected plain JS checker set, got {output['qa_checkers']}"


def test_python_project_gets_full_checker_set(tmp_path):
    """Project with requirements.txt → qa_checkers=['pytest', 'mypy', 'ruff']."""
    target = tmp_path / "py_project"
    target.mkdir()
    (target / "requirements.txt").write_text("pytest==7.0.0\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["qa_checkers"] == ["pytest", "mypy", "ruff"], \
        f"Expected full Python checker set, got {output['qa_checkers']}"


def test_ruby_project_gets_full_checker_set(tmp_path):
    """Project with Gemfile → qa_checkers=['rspec', 'rubocop']."""
    target = tmp_path / "rb_project"
    target.mkdir()
    (target / "Gemfile").write_text("gem 'rspec'\n")
    
    script_path = Path(__file__).parent.parent / "scripts" / "analyze_project.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(target)],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert output["qa_checkers"] == ["rspec", "rubocop"], \
        f"Expected full Ruby checker set, got {output['qa_checkers']}"


def test_unknown_stack_has_bootstrap_flag(tmp_path):
    """Empty temp dir → qa_bootstrap_needed=True."""
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
    assert output["qa_bootstrap_needed"] == True, f"Expected qa_bootstrap_needed=True, got {output.get('qa_bootstrap_needed')}"
    assert output["stack"] == "unknown", f"Expected stack='unknown', got {output['stack']}"
