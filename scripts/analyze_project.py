#!/usr/bin/env python3
"""Deterministic project analysis script.

Scans a project and produces a structured JSON report: stack detection,
agent file detection, directory structure analysis, git state, existing
pipeline files, test command detection, and deployment hints.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def detect_test_command(target: Path) -> tuple[str, str]:
    """Detect test command and corresponding qa_checker name.
    
    Args:
        target: Path to the project
    
    Returns:
        Tuple of (test_command, qa_checker). Both are "unknown" if no match.
    
    Detection rules (highest-priority match wins):
    - Gemfile → ("bundle exec rspec", "rspec")
    - package.json → ("npm test", "jest")
    - pom.xml → ("mvn test", "maven")
    - build.gradle or build.gradle.kts → ("./gradlew test", "gradle")
    - requirements.txt/pyproject.toml/setup.py → ("pytest", "pytest")
    - none → ("unknown", "unknown")
    """
    # Check in priority order
    if (target / "Gemfile").exists():
        return ("bundle exec rspec", "rspec")
    if (target / "package.json").exists():
        return ("npm test", "jest")
    if (target / "pom.xml").exists():
        return ("mvn test", "maven")
    if (target / "build.gradle").exists() or (target / "build.gradle.kts").exists():
        return ("./gradlew test", "gradle")
    if (target / "requirements.txt").exists() or (target / "pyproject.toml").exists() or (target / "setup.py").exists():
        return ("pytest", "pytest")
    
    return ("unknown", "unknown")


def detect_deploy_hints(target: Path) -> list[str]:
    """Detect deployment hints from project files and structure.
    
    Args:
        target: Path to the project
    
    Returns:
        List of deployment hint strings. Returns ["unknown"] if none found.
    
    Detection rules:
    - .github/workflows/ directory exists → "github-actions"
    - Dockerfile or docker-compose.yml exists → "dockerfile"
    - Makefile with a 'deploy' target → "makefile-deploy-target"
    - Procfile exists → "heroku"
    - *.sh file with 'deploy' or 'scp' in name → "scp-script"
    - none → ["unknown"]
    """
    hints = []
    
    # Check for GitHub Actions
    if (target / ".github" / "workflows").exists() and (target / ".github" / "workflows").is_dir():
        hints.append("github-actions")
    
    # Check for Docker
    if (target / "Dockerfile").exists() or (target / "docker-compose.yml").exists():
        hints.append("dockerfile")
    
    # Check for Makefile with deploy target
    makefile_path = target / "Makefile"
    if makefile_path.exists():
        try:
            content = makefile_path.read_text()
            if "deploy:" in content or "deploy :" in content:
                hints.append("makefile-deploy-target")
        except (IOError, UnicodeDecodeError):
            pass
    
    # Check for Procfile (Heroku)
    if (target / "Procfile").exists():
        hints.append("heroku")
    
    # Check for deploy/scp scripts
    for script_file in target.glob("*.sh"):
        if "deploy" in script_file.name.lower() or "scp" in script_file.name.lower():
            hints.append("scp-script")
            break
    
    # Return hints or unknown
    return hints if hints else ["unknown"]



def analyze_project(target_path: str) -> dict:
    """Analyze a project and return structured findings.
    
    Args:
        target_path: Path to the project to analyze
    
    Returns:
        Dictionary with analysis results containing:
        - project_name: Name of the project (directory name)
        - stack: Detected stack ("python", "javascript", "ruby", "java", "mixed", "unknown")
        - agent_file: Dict with type and content
        - structure: Dict with present directories
        - git: Dict with git state
        - missing: List of missing pipeline directories
        - existing_pipeline_files: List of existing pipeline files
        - test_command: Detected or inferred test command string
        - qa_checker: Corresponding qa_compress.py checker name
        - deploy_hints: List of deployment signals found
    """
    target = Path(target_path).resolve()
    
    # Detect stack
    stack_markers = {
        "python": ["requirements.txt", "pyproject.toml", "setup.py"],
        "javascript": ["package.json"],
        "ruby": ["Gemfile"],
        "java": ["pom.xml", "build.gradle"],
    }
    
    detected_stacks = []
    for stack_type, markers in stack_markers.items():
        for marker in markers:
            if (target / marker).exists():
                detected_stacks.append(stack_type)
                break
    
    # Determine final stack
    if len(detected_stacks) == 0:
        stack = "unknown"
    elif len(detected_stacks) == 1:
        stack = detected_stacks[0]
    else:
        stack = "mixed"
    
    # Detect agent file
    agent_file = {"type": "none", "content": None}
    if (target / "AGENTS.md").exists():
        agent_file["type"] = "agents.md"
        agent_file["content"] = (target / "AGENTS.md").read_text()
    elif (target / "CLAUDE.md").exists():
        agent_file["type"] = "claude.md"
        agent_file["content"] = (target / "CLAUDE.md").read_text()
    
    # Check directory structure
    pipeline_dirs = [
        "src/core",
        "src/adapters",
        "tests",
        "tests/fakes",
        "docs",
        "docs/features",
        ".pipeline",
    ]
    
    present_dirs = []
    missing_dirs = []
    
    for dir_name in pipeline_dirs:
        dir_path = target / dir_name
        if dir_path.exists() and dir_path.is_dir():
            present_dirs.append(dir_name)
        else:
            missing_dirs.append(dir_name)
    
    # Get git state
    git_state = {
        "current_branch": None,
        "branches": [],
        "has_main": False,
        "has_master": False,
        "remotes": [],
    }
    
    git_dir = target / ".git"
    if git_dir.exists():
        # Get current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            git_state["current_branch"] = result.stdout.strip()
        
        # Get all branches
        result = subprocess.run(
            ["git", "branch", "-a"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            branches = [line.strip().lstrip("* ") for line in result.stdout.strip().split("\n") if line.strip()]
            git_state["branches"] = branches
            
            # Check for main/master
            git_state["has_main"] = any("main" in b for b in branches)
            git_state["has_master"] = any("master" in b for b in branches)
        
        # Get remotes
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            remotes = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split()
                    if parts:
                        remotes.append(parts[0])
            git_state["remotes"] = list(set(remotes))  # Remove duplicates
    
    # Check existing pipeline files
    pipeline_files = [
        "STORIES.md",
        "FEATURES.md",
        "qa_config.json",
        ".pipeline/intent.json",
    ]
    
    existing_files = []
    for file_name in pipeline_files:
        file_path = target / file_name
        if file_path.exists():
            existing_files.append(file_name)
    
    # Detect test command and qa_checker
    test_command, qa_checker = detect_test_command(target)
    
    # Detect deploy hints
    deploy_hints = detect_deploy_hints(target)
    
    # Build result
    result = {
        "project_name": target.name,
        "stack": stack,
        "agent_file": agent_file,
        "structure": {
            "present": present_dirs,
            "total_expected": len(pipeline_dirs),
        },
        "git": git_state,
        "missing": missing_dirs,
        "existing_pipeline_files": existing_files,
        "test_command": test_command,
        "qa_checker": qa_checker,
        "deploy_hints": deploy_hints,
    }
    
    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze a project and output structured JSON report"
    )
    parser.add_argument(
        "target_path",
        help="Path to the project to analyze"
    )
    
    args = parser.parse_args()
    
    target = Path(args.target_path).resolve()
    
    # Check if path exists
    if not target.exists():
        sys.exit(1)
    
    # Check if path is a directory
    if not target.is_dir():
        sys.exit(2)
    
    # Analyze and output
    result = analyze_project(str(target))
    print(json.dumps(result, indent=2))
    
    sys.exit(0)


if __name__ == "__main__":
    main()
