#!/usr/bin/env python3
"""Validate a migrated project against pipeline expectations.

This script runs deterministic checks on a project to ensure it has been
properly migrated to the opencode pipeline. It validates:
- AGENTS.md exists and constant sections match template
- Required directories exist (.pipeline/, docs/features/, tests/)
- qa_config.json exists and contains valid checker names
- FEATURES.md exists
- STORIES.md exists
- .pipeline/intent.json exists
- Git is initialized

Exit codes:
  0 - PASS: all checks pass
  1 - FAIL: one or more checks fail
  2 - ERROR: path doesn't exist
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Valid checker names
VALID_CHECKERS = {
    "pytest",
    "rspec",
    "jest",
    "gradle",
    "maven",
    "json",
    "yaml",
    "html",
}

# Required directories
REQUIRED_DIRS = [
    ".pipeline",
    "docs/features",
    "tests",
]


def extract_sections(content: str) -> Dict[str, str]:
    """Extract constant sections from markdown content.
    
    Returns a dict mapping section name to section content (including heading).
    """
    constant_sections = [
        "## Workflow",
        "## Git conventions",
        "## Languages",
        "## Prohibitions",
    ]
    
    sections = {}
    lines = content.split('\n')
    
    for section_heading in constant_sections:
        section_name = section_heading.replace("## ", "")
        start_idx = None
        end_idx = None
        
        # Find section start
        for i, line in enumerate(lines):
            if line.strip() == section_heading.strip():
                start_idx = i
                break
        
        if start_idx is None:
            continue
        
        # Find section end (next ## heading or end of file)
        for i in range(start_idx + 1, len(lines)):
            if lines[i].startswith("## "):
                end_idx = i
                break
        
        if end_idx is None:
            end_idx = len(lines)
        
        # Extract section content
        section_lines = lines[start_idx:end_idx]
        section_content = '\n'.join(section_lines)
        sections[section_name] = section_content
    
    return sections


def normalize_lines(text: str) -> List[str]:
    """Normalize text by stripping trailing whitespace per line."""
    return [line.rstrip() for line in text.split('\n')]


def compare_sections(template_sections: Dict[str, str], 
                    project_sections: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Compare sections between template and project.
    
    Returns (is_identical, list_of_different_sections).
    """
    constant_sections = [
        "## Workflow",
        "## Git conventions",
        "## Languages",
        "## Prohibitions",
    ]
    
    different_sections = []
    
    for section_heading in constant_sections:
        section_key = section_heading.replace("## ", "")
        
        template_content = template_sections.get(section_key, "")
        project_content = project_sections.get(section_key, "")
        
        template_lines = normalize_lines(template_content)
        project_lines = normalize_lines(project_content)
        
        if template_lines != project_lines:
            different_sections.append(section_key)
    
    is_identical = len(different_sections) == 0
    return is_identical, different_sections


def check_agents_md(target_path: Path) -> Dict:
    """Check if AGENTS.md exists."""
    agents_path = target_path / "AGENTS.md"
    
    if agents_path.exists():
        return {
            "check": "agents_md",
            "status": "pass",
            "detail": "AGENTS.md exists"
        }
    else:
        return {
            "check": "agents_md",
            "status": "fail",
            "detail": "AGENTS.md not found"
        }


def check_template_constancy(target_path: Path) -> Dict:
    """Check if AGENTS.md constant sections match template."""
    agents_path = target_path / "AGENTS.md"
    
    if not agents_path.exists():
        return {
            "check": "template_constancy",
            "status": "fail",
            "detail": "AGENTS.md not found (cannot check constancy)"
        }
    
    # Find template AGENTS.md
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    template_path = repo_root / "templates" / "AGENTS.md"
    
    if not template_path.exists():
        return {
            "check": "template_constancy",
            "status": "fail",
            "detail": f"Template AGENTS.md not found at {template_path}"
        }
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        with open(agents_path, 'r', encoding='utf-8') as f:
            project_content = f.read()
    except Exception as e:
        return {
            "check": "template_constancy",
            "status": "fail",
            "detail": f"Error reading files: {e}"
        }
    
    # Extract and compare sections
    template_sections = extract_sections(template_content)
    project_sections = extract_sections(project_content)
    
    is_identical, different_sections = compare_sections(template_sections, project_sections)
    
    if is_identical:
        return {
            "check": "template_constancy",
            "status": "pass",
            "detail": "Constant sections match template"
        }
    else:
        return {
            "check": "template_constancy",
            "status": "fail",
            "detail": f"Sections differ: {', '.join(different_sections)}"
        }


def check_required_dirs(target_path: Path) -> Dict:
    """Check if required directories exist."""
    missing_dirs = []
    
    for dir_name in REQUIRED_DIRS:
        dir_path = target_path / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
    
    if not missing_dirs:
        return {
            "check": "required_dirs",
            "status": "pass",
            "detail": f"All required directories exist: {', '.join(REQUIRED_DIRS)}"
        }
    else:
        return {
            "check": "required_dirs",
            "status": "fail",
            "detail": f"Missing directories: {', '.join(missing_dirs)}"
        }


def check_qa_config(target_path: Path) -> Dict:
    """Check if qa_config.json exists and contains valid checker names."""
    qa_config_path = target_path / "qa_config.json"
    
    if not qa_config_path.exists():
        return {
            "check": "qa_config",
            "status": "fail",
            "detail": "qa_config.json not found"
        }
    
    try:
        with open(qa_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        return {
            "check": "qa_config",
            "status": "fail",
            "detail": f"Error reading qa_config.json: {e}"
        }
    
    # Check if checkers key exists
    if "checkers" not in config:
        return {
            "check": "qa_config",
            "status": "fail",
            "detail": "qa_config.json missing 'checkers' key"
        }
    
    checkers = config["checkers"]
    
    # Validate each checker
    invalid_checkers = []
    for checker in checkers:
        if checker not in VALID_CHECKERS:
            invalid_checkers.append(checker)
    
    if invalid_checkers:
        return {
            "check": "qa_config",
            "status": "fail",
            "detail": f"Invalid checkers: {', '.join(invalid_checkers)}. Valid: {', '.join(sorted(VALID_CHECKERS))}"
        }
    
    return {
        "check": "qa_config",
        "status": "pass",
        "detail": f"qa_config.json valid with checkers: {', '.join(checkers)}"
    }


def check_features_md(target_path: Path) -> Dict:
    """Check if FEATURES.md exists."""
    features_path = target_path / "FEATURES.md"
    
    if features_path.exists():
        return {
            "check": "features_md",
            "status": "pass",
            "detail": "FEATURES.md exists"
        }
    else:
        return {
            "check": "features_md",
            "status": "fail",
            "detail": "FEATURES.md not found"
        }


def check_stories_md(target_path: Path) -> Dict:
    """Check if STORIES.md exists."""
    stories_path = target_path / "STORIES.md"
    
    if stories_path.exists():
        return {
            "check": "stories_md",
            "status": "pass",
            "detail": "STORIES.md exists"
        }
    else:
        return {
            "check": "stories_md",
            "status": "fail",
            "detail": "STORIES.md not found"
        }


def check_pipeline_intent(target_path: Path) -> Dict:
    """Check if .pipeline/intent.json exists."""
    intent_path = target_path / ".pipeline" / "intent.json"
    
    if intent_path.exists():
        return {
            "check": "pipeline_intent",
            "status": "pass",
            "detail": ".pipeline/intent.json exists"
        }
    else:
        return {
            "check": "pipeline_intent",
            "status": "fail",
            "detail": ".pipeline/intent.json not found"
        }


def check_git_initialized(target_path: Path) -> Dict:
    """Check if git is initialized."""
    git_dir = target_path / ".git"
    
    if git_dir.exists():
        return {
            "check": "git_initialized",
            "status": "pass",
            "detail": "Git is initialized (.git directory exists)"
        }
    else:
        return {
            "check": "git_initialized",
            "status": "fail",
            "detail": ".git directory not found"
        }


def validate_migration(target_path: str) -> Dict:
    """Run all validation checks on a project.
    
    Args:
        target_path: Path to the project to validate
    
    Returns:
        Dict with overall status and per-check results
    """
    target = Path(target_path)
    
    if not target.exists():
        return {
            "status": "FAIL",
            "error": f"Path does not exist: {target_path}",
            "checks": []
        }
    
    # Run all checks
    checks = [
        check_agents_md(target),
        check_template_constancy(target),
        check_required_dirs(target),
        check_qa_config(target),
        check_features_md(target),
        check_stories_md(target),
        check_pipeline_intent(target),
        check_git_initialized(target),
    ]
    
    # Determine overall status
    all_pass = all(check["status"] == "pass" for check in checks)
    overall_status = "PASS" if all_pass else "FAIL"
    
    return {
        "status": overall_status,
        "checks": checks
    }


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "FAIL",
            "error": "Usage: validate_migration.py <path>"
        }))
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    # Check if path exists
    if not Path(target_path).exists():
        print(json.dumps({
            "status": "FAIL",
            "error": f"Path does not exist: {target_path}",
            "checks": []
        }))
        sys.exit(2)
    
    # Run validation
    result = validate_migration(target_path)
    
    # Output JSON
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    if result["status"] == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
