"""Tests for validate_migration.py script."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest


@pytest.fixture
def scripts_dir():
    """Return the scripts directory."""
    return Path(__file__).parent.parent / "scripts"


@pytest.fixture
def templates_dir():
    """Return the templates directory."""
    return Path(__file__).parent.parent / "templates"


@pytest.fixture
def template_agents_md(templates_dir):
    """Read the actual template AGENTS.md."""
    template_path = templates_dir / "AGENTS.md"
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def valid_project(tmp_path, template_agents_md):
    """Create a valid project structure with all required files/dirs.
    
    Returns the project root path.
    """
    project_root = tmp_path / "valid_project"
    project_root.mkdir()
    
    # Create AGENTS.md with correct constant sections
    agents_md_path = project_root / "AGENTS.md"
    agents_md_path.write_text(template_agents_md, encoding='utf-8')
    
    # Create required directories
    (project_root / ".pipeline").mkdir()
    (project_root / "docs" / "features").mkdir(parents=True)
    (project_root / "tests").mkdir()
    
    # Create .pipeline/intent.json
    intent_json = project_root / ".pipeline" / "intent.json"
    intent_json.write_text(json.dumps({"step": "test"}), encoding='utf-8')
    
    # Create qa_config.json with valid checkers
    qa_config = project_root / "qa_config.json"
    qa_config.write_text(json.dumps({"checkers": ["pytest"]}), encoding='utf-8')
    
    # Create FEATURES.md
    features_md = project_root / "FEATURES.md"
    features_md.write_text("# Features\n", encoding='utf-8')
    
    # Create STORIES.md
    stories_md = project_root / "STORIES.md"
    stories_md.write_text("# Stories\n", encoding='utf-8')
    
    # Initialize git
    subprocess.run(
        ["git", "init"],
        cwd=project_root,
        capture_output=True,
        check=True
    )
    
    return project_root


def run_validate_migration(target_path: str) -> tuple:
    """Run validate_migration.py and return (returncode, stdout, stderr)."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "validate_migration.py"), target_path],
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


class TestValidateMigration:
    """Tests for validate_migration.py."""
    
    def test_script_exists(self, scripts_dir):
        """Script exists and is executable."""
        script_path = scripts_dir / "validate_migration.py"
        assert script_path.exists(), f"validate_migration.py not found at {script_path}"
    
    def test_fully_valid_project(self, valid_project):
        """Valid project with all required files/dirs -> overall PASS."""
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 0, f"Expected exit code 0, got {returncode}. stderr: {stderr}"
        
        output = json.loads(stdout)
        assert output["status"] == "PASS", f"Expected status PASS, got {output['status']}"
        assert "checks" in output
        
        # All checks should pass
        for check in output["checks"]:
            assert check["status"] == "pass", f"Check {check['check']} failed: {check['detail']}"
    
    def test_missing_agents_md(self, valid_project):
        """Missing AGENTS.md -> overall FAIL, agents_md check fails."""
        (valid_project / "AGENTS.md").unlink()
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 1, f"Expected exit code 1, got {returncode}"
        
        output = json.loads(stdout)
        assert output["status"] == "FAIL"
        
        # Find the agents_md check
        agents_check = next((c for c in output["checks"] if c["check"] == "agents_md"), None)
        assert agents_check is not None, "agents_md check not found"
        assert agents_check["status"] == "fail"
    
    def test_missing_qa_config(self, valid_project):
        """Missing qa_config.json -> overall FAIL, qa_config check fails."""
        (valid_project / "qa_config.json").unlink()
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 1
        
        output = json.loads(stdout)
        assert output["status"] == "FAIL"
        
        qa_check = next((c for c in output["checks"] if c["check"] == "qa_config"), None)
        assert qa_check is not None
        assert qa_check["status"] == "fail"
    
    def test_missing_pipeline_dir(self, valid_project):
        """Missing .pipeline/ -> overall FAIL."""
        import shutil
        shutil.rmtree(valid_project / ".pipeline")
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 1
        
        output = json.loads(stdout)
        assert output["status"] == "FAIL"
    
    def test_invalid_qa_config_nonexistent_checker(self, valid_project):
        """qa_config.json with invalid checker name -> overall FAIL."""
        qa_config = valid_project / "qa_config.json"
        qa_config.write_text(json.dumps({"checkers": ["nonexistent"]}), encoding='utf-8')
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 1
        
        output = json.loads(stdout)
        assert output["status"] == "FAIL"
        
        qa_check = next((c for c in output["checks"] if c["check"] == "qa_config"), None)
        assert qa_check is not None
        assert qa_check["status"] == "fail"
    
    def test_valid_qa_config_pytest(self, valid_project):
        """qa_config.json with valid checker pytest -> qa_config check passes."""
        qa_config = valid_project / "qa_config.json"
        qa_config.write_text(json.dumps({"checkers": ["pytest"]}), encoding='utf-8')
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 0
        
        output = json.loads(stdout)
        qa_check = next((c for c in output["checks"] if c["check"] == "qa_config"), None)
        assert qa_check is not None
        assert qa_check["status"] == "pass"
    
    def test_valid_qa_config_multiple_checkers(self, valid_project):
        """qa_config.json with multiple valid checkers -> qa_config check passes."""
        qa_config = valid_project / "qa_config.json"
        qa_config.write_text(
            json.dumps({"checkers": ["pytest", "rspec", "jest"]}),
            encoding='utf-8'
        )
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 0
        
        output = json.loads(stdout)
        qa_check = next((c for c in output["checks"] if c["check"] == "qa_config"), None)
        assert qa_check is not None
        assert qa_check["status"] == "pass"
    
    def test_missing_features_md(self, valid_project):
        """Missing FEATURES.md -> overall FAIL."""
        (valid_project / "FEATURES.md").unlink()
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 1
        
        output = json.loads(stdout)
        assert output["status"] == "FAIL"
        
        features_check = next((c for c in output["checks"] if c["check"] == "features_md"), None)
        assert features_check is not None
        assert features_check["status"] == "fail"
    
    def test_missing_stories_md(self, valid_project):
        """Missing STORIES.md -> overall FAIL."""
        (valid_project / "STORIES.md").unlink()
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 1
        
        output = json.loads(stdout)
        assert output["status"] == "FAIL"
        
        stories_check = next((c for c in output["checks"] if c["check"] == "stories_md"), None)
        assert stories_check is not None
        assert stories_check["status"] == "fail"
    
    def test_template_constancy_pass(self, valid_project, template_agents_md):
        """AGENTS.md matching template sections -> template_constancy check passes."""
        # valid_project already has the correct template, so this should pass
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 0
        
        output = json.loads(stdout)
        constancy_check = next(
            (c for c in output["checks"] if c["check"] == "template_constancy"),
            None
        )
        assert constancy_check is not None
        assert constancy_check["status"] == "pass"
    
    def test_template_constancy_fail_wrong_workflow(self, valid_project):
        """AGENTS.md with wrong Workflow section -> template_constancy check fails."""
        agents_md = valid_project / "AGENTS.md"
        content = agents_md.read_text(encoding='utf-8')
        
        # Replace the Workflow section with something wrong
        wrong_content = content.replace(
            "## Workflow",
            "## Workflow (WRONG)"
        )
        agents_md.write_text(wrong_content, encoding='utf-8')
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 1
        
        output = json.loads(stdout)
        assert output["status"] == "FAIL"
        
        constancy_check = next(
            (c for c in output["checks"] if c["check"] == "template_constancy"),
            None
        )
        assert constancy_check is not None
        assert constancy_check["status"] == "fail"
    
    def test_nonexistent_path(self):
        """Nonexistent path -> exit code 2."""
        returncode, stdout, stderr = run_validate_migration("/nonexistent/path/to/project")
        
        assert returncode == 2, f"Expected exit code 2, got {returncode}"
    
    def test_missing_required_dirs(self, valid_project):
        """Missing required directories -> overall FAIL."""
        import shutil
        shutil.rmtree(valid_project / "docs")
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 1
        
        output = json.loads(stdout)
        assert output["status"] == "FAIL"
    
    def test_missing_git_dir(self, valid_project):
        """Missing .git/ -> overall FAIL."""
        import shutil
        shutil.rmtree(valid_project / ".git")
        
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        assert returncode == 1
        
        output = json.loads(stdout)
        assert output["status"] == "FAIL"
        
        git_check = next((c for c in output["checks"] if c["check"] == "git_initialized"), None)
        assert git_check is not None
        assert git_check["status"] == "fail"
    
    def test_output_json_structure(self, valid_project):
        """Output JSON has correct structure."""
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        output = json.loads(stdout)
        
        # Check top-level structure
        assert "status" in output
        assert "checks" in output
        assert output["status"] in ["PASS", "FAIL"]
        
        # Check each check structure
        for check in output["checks"]:
            assert "check" in check
            assert "status" in check
            assert "detail" in check
            assert check["status"] in ["pass", "fail"]
    
    def test_all_checks_present(self, valid_project):
        """All expected checks are present in output."""
        returncode, stdout, stderr = run_validate_migration(str(valid_project))
        
        output = json.loads(stdout)
        
        expected_checks = [
            "agents_md",
            "template_constancy",
            "required_dirs",
            "qa_config",
            "features_md",
            "stories_md",
            "pipeline_intent",
            "git_initialized",
        ]
        
        check_names = [c["check"] for c in output["checks"]]
        
        for expected in expected_checks:
            assert expected in check_names, f"Expected check '{expected}' not found in output"
