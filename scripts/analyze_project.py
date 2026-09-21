#!/usr/bin/env python3
"""Deterministic project analysis script.

Scans a project and produces a structured JSON report: stack detection,
agent file detection, directory structure analysis, git state, and
existing pipeline files.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


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
