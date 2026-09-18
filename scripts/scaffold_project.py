#!/usr/bin/env python3
"""Deterministic project scaffolding script.

Creates a complete project skeleton by copying templates and creating directories.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def scaffold_project(target_path: str, project_name: str | None = None, stack: str = "python") -> int:
    """Scaffold a new project at target_path.
    
    Args:
        target_path: Path where to create the project
        project_name: Optional project name (defaults to directory name)
        stack: Stack hint (python|ruby|javascript|java|mixed) — determines
               the created directory set (deterministic, no stack guessing)
    
    Returns:
        0 on success
        1 if target doesn't exist
        2 if already scaffolded (AGENTS.md exists)
    """
    target = Path(target_path).resolve()
    
    # Check if target exists
    if not target.exists():
        return 1
    
    # Check if already scaffolded
    if (target / "AGENTS.md").exists():
        return 2
    
    # Get project name
    if project_name is None:
        project_name = target.name
    
    # Initialize git if needed
    git_dir = target / ".git"
    if not git_dir.exists():
        subprocess.run(
            ["git", "init"],
            cwd=target,
            capture_output=True,
            check=True
        )
        subprocess.run(
            ["git", "checkout", "-b", "main"],
            cwd=target,
            capture_output=True,
            check=False  # May fail if already on main
        )
    
    # Create directories — stack-aware, deterministic (no stack guessing)
    stack_dirs = {
        "python": ["docs", "docs/features", "tests", "tests/fakes", "src/core", "src/adapters"],
        "ruby": ["docs", "docs/features", "spec", "src"],
        "javascript": ["docs", "docs/features", "test", "src"],
        "java": ["docs", "docs/features", "src/test", "src/main"],
        "mixed": ["docs", "docs/features", "src", "tests"],
    }
    if stack not in stack_dirs:
        raise ValueError(f"unknown stack: {stack} (expected one of {sorted(stack_dirs)})")
    directories = stack_dirs[stack] + [".pipeline"]
    
    created_files = []
    
    for dir_name in directories:
        dir_path = target / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        created_files.append(str(dir_path.relative_to(target)))
    
    # Get script directory (where this script is located)
    script_dir = Path(__file__).parent.parent
    
    # Copy templates
    templates_to_copy = [
        ("templates/AGENTS.md", "AGENTS.md"),
        ("docs/features/_story_template.md", "docs/features/_story_template.md"),
        ("templates/.gitignore", ".gitignore"),
    ]
    
    for src_rel, dst_rel in templates_to_copy:
        src = script_dir / src_rel
        dst = target / dst_rel
        
        if src.exists():
            # Ensure parent directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
            created_files.append(str(dst.relative_to(target)))
    
    # Create starter files
    starter_files = {
        "FEATURES.md": "# Features\n\n",
        "docs/requirements.md": "# Requirements\n\n",
        "docs/design.md": "# Design\n\n",
        "README.md": f"# {project_name}\n\n",
    }
    
    for file_rel, content in starter_files.items():
        file_path = target / file_rel
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.write_text(content)
            created_files.append(str(file_path.relative_to(target)))
    
    # Create qa_config.json (default checkers — architect/user adapts per project stack)
    qa_config_file = target / "qa_config.json"
    if not qa_config_file.exists():
        qa_config = {"checkers": ["pytest"]}
        qa_config_file.write_text(json.dumps(qa_config, indent=2) + "\n")
        created_files.append(str(qa_config_file.relative_to(target)))

    # Create .pipeline/intent.json
    intent_file = target / ".pipeline" / "intent.json"
    intent_file.parent.mkdir(parents=True, exist_ok=True)
    intent_content = {
        "project": project_name,
        "created": True
    }
    intent_file.write_text(json.dumps(intent_content, indent=2))
    created_files.append(str(intent_file.relative_to(target)))
    
    # Output JSON
    output = {
        "created": created_files,
        "target": str(target)
    }
    print(json.dumps(output))
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scaffold a new opencode pipeline project"
    )
    parser.add_argument(
        "target_path",
        help="Path where to create the project"
    )
    parser.add_argument(
        "--name",
        help="Project name (defaults to directory name)"
    )
    parser.add_argument(
        "--stack",
        choices=["python", "ruby", "javascript", "java", "mixed"],
        default="python",
        help="Stack hint deciding the directory layout (default: python)"
    )
    
    args = parser.parse_args()
    
    exit_code = scaffold_project(args.target_path, args.name, args.stack)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
