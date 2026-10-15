#!/usr/bin/env python3
"""
provision_structure.py — Deterministic structure provisioning for opencode projects.

Creates missing directories and files based on analysis JSON. Never overwrites existing files.
Uses analysis from Story 12-02 to know what's already present.

Accepts optional qa_checkers list and deploy_methods to write qa_config.json and append
## Deployment section to AGENTS.md.

Updated in Story 27-05: Accepts qa_checkers (list) instead of qa_checker (string).
Writes complete checker list to qa_config.json.

Usage:
    python provision_structure.py <target_path> <analysis_json_file>
    provision_structure(target_path, analysis, qa_checkers=["pytest", "mypy"], deploy_methods=["docker"])

Exit codes:
    0 — Success
    1 — Target path doesn't exist
"""

import json
import sys
from pathlib import Path


def provision_structure(target_path: str, analysis: dict, qa_checkers: list = [], deploy_methods: list = []) -> dict:
    """
    Create missing directories and files for a project.
    
    Args:
        target_path: Path to the project directory
        analysis: Analysis dict from Story 12-02 with structure info
        qa_checkers: Optional list of checker names (e.g., ["pytest", "mypy", "ruff"]).
                    If set and not empty, qa_config.json is written with these checkers.
                    If analysis contains "qa_bootstrap_needed": true, writes bootstrap config.
        deploy_methods: Optional list of deployment methods (e.g., ["docker", "scp"])
        
    Returns:
        Report dict with "created", "already_existed", "gitignore_entries_added", "qa_config", "deploy_section" keys
    """
    target = Path(target_path)
    
    if not target.exists():
        return {"error": "Target path does not exist"}
    
    report = {
        "created": [],
        "already_existed": [],
        "gitignore_entries_added": [],
        "qa_config": "skipped",
        "deploy_section": "skipped"
    }
    
    # Directories to create
    directories = [
        ".pipeline",
        "docs",
        "docs/features",
        "tests",
        "tests/fakes",
        "src/core",
        "src/adapters",
        ".worktrees"
    ]
    
    # Create missing directories
    for dir_name in directories:
        dir_path = target / dir_name
        if dir_path.exists():
            report["already_existed"].append(dir_name)
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            report["created"].append(dir_name)
    
    # Stack to checkers mapping (full sets per stack)
    stack_to_checkers = {
        "python": ["pytest", "mypy", "ruff"],
        "javascript": ["jest", "eslint", "prettier", "npm-audit"],
        "ruby": ["rspec", "rubocop"],
        "java": ["gradle", "checkstyle"],
        "mixed": ["pytest"],
        "unknown": ["pytest"]
    }
    
    # Determine checkers based on qa_checkers param or analysis
    checkers_to_use = []
    if qa_checkers:
        # Use provided qa_checkers list
        checkers_to_use = qa_checkers
    else:
        # Determine from stack in analysis
        stack = analysis.get("stack", "unknown")
        checkers_to_use = stack_to_checkers.get(stack, ["pytest"])
    
    # Create qa_config.json
    qa_config_path = target / "qa_config.json"
    
    # Check if bootstrap is needed (unknown stack from analysis)
    qa_bootstrap_needed = analysis.get("qa_bootstrap_needed", False)
    
    if qa_checkers or not qa_bootstrap_needed:
        # Standard case: write qa_config.json with checkers
        if not qa_config_path.exists():
            qa_config = {"checkers": checkers_to_use}
            qa_config_path.write_text(json.dumps(qa_config, indent=2))
            report["qa_config"] = "created"
        else:
            report["qa_config"] = "skipped"
    elif qa_bootstrap_needed:
        # Bootstrap case: write placeholder config with _bootstrap_needed flag
        if not qa_config_path.exists():
            qa_config = {
                "checkers": ["pytest"],
                "_bootstrap_needed": True,
                "_reason": "unknown stack — architect must research test tooling and update qa_config.json"
            }
            qa_config_path.write_text(json.dumps(qa_config, indent=2))
            report["qa_config"] = "created"
        else:
            report["qa_config"] = "skipped"
    
    # Create .pipeline/intent.json if it doesn't exist
    intent_path = target / ".pipeline" / "intent.json"
    if not intent_path.exists():
        project_name = analysis.get("project_name", "unknown")
        intent = {
            "project": project_name,
            "created": True
        }
        intent_path.write_text(json.dumps(intent, indent=2))
        report["created"].append(".pipeline/intent.json")
    else:
        report["already_existed"].append(".pipeline/intent.json")
    
    # Get the pipeline repo root (parent of scripts dir)
    pipeline_root = Path(__file__).parent.parent
    
    # Copy story template if it doesn't exist
    story_template_src = pipeline_root / "docs" / "features" / "_story_template.md"
    story_template_dst = target / "docs" / "features" / "_story_template.md"
    
    if story_template_src.exists():
        if not story_template_dst.exists():
            story_template_dst.write_text(story_template_src.read_text())
            report["created"].append("docs/features/_story_template.md")
        else:
            report["already_existed"].append("docs/features/_story_template.md")
    
    # Copy feature template if it doesn't exist
    feature_template_src = pipeline_root / "docs" / "features" / "_feature_template.md"
    feature_template_dst = target / "docs" / "features" / "_feature_template.md"
    
    if feature_template_src.exists():
        if not feature_template_dst.exists():
            feature_template_dst.write_text(feature_template_src.read_text())
            report["created"].append("docs/features/_feature_template.md")
        else:
            report["already_existed"].append("docs/features/_feature_template.md")
    
    # Create FEATURES.md if it doesn't exist
    features_path = target / "FEATURES.md"
    if not features_path.exists():
        features_path.write_text("# Features\n\n")
        report["created"].append("FEATURES.md")
    else:
        report["already_existed"].append("FEATURES.md")
    
    # Create STORIES.md if it doesn't exist
    stories_path = target / "STORIES.md"
    if not stories_path.exists():
        stories_path.write_text("# Stories\n\n")
        report["created"].append("STORIES.md")
    else:
        report["already_existed"].append("STORIES.md")
    
    # Handle .gitignore merge
    gitignore_path = target / ".gitignore"
    pipeline_entries = [".pipeline/", ".worktrees/", "*.log", "__pycache__/", ".pytest_cache/"]
    
    if gitignore_path.exists():
        # Read existing .gitignore
        existing_content = gitignore_path.read_text()
        existing_lines = set(line.strip() for line in existing_content.split("\n") if line.strip())
        
        # Add missing entries
        new_lines = []
        for entry in pipeline_entries:
            if entry not in existing_lines:
                new_lines.append(entry)
                report["gitignore_entries_added"].append(entry)
        
        # Append new entries if any
        if new_lines:
            if existing_content and not existing_content.endswith("\n"):
                gitignore_path.write_text(existing_content + "\n" + "\n".join(new_lines) + "\n")
            else:
                gitignore_path.write_text(existing_content + "\n".join(new_lines) + "\n")
    else:
        # Create new .gitignore
        gitignore_content = "\n".join(pipeline_entries) + "\n"
        gitignore_path.write_text(gitignore_content)
        report["gitignore_entries_added"] = pipeline_entries
        report["created"].append(".gitignore")
    
    # Append ## Deployment section to AGENTS.md if deploy_methods provided
    agents_md_path = target / "AGENTS.md"
    if deploy_methods and agents_md_path.exists():
        agents_md_content = agents_md_path.read_text()
        
        # Check if ## Deployment section already exists
        if "## Deployment" not in agents_md_content:
            # Append the deployment section
            deployment_section = "\n## Deployment\n\n"
            deployment_section += "This project uses the following deployment methods:\n\n"
            for method in deploy_methods:
                deployment_section += f"- **{method}**\n"
            deployment_section += "\n"
            
            agents_md_path.write_text(agents_md_content + deployment_section)
            report["deploy_section"] = "created"
        else:
            report["deploy_section"] = "skipped"
    
    return report


def main():
    """CLI entry point."""
    if len(sys.argv) != 3:
        print("Usage: provision_structure.py <target_path> <analysis_json_file>", file=sys.stderr)
        sys.exit(1)
    
    target_path = sys.argv[1]
    analysis_file = sys.argv[2]
    
    # Check if target path exists
    if not Path(target_path).exists():
        sys.exit(1)
    
    # Load analysis JSON
    try:
        with open(analysis_file) as f:
            analysis = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading analysis file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run provisioning
    report = provision_structure(target_path, analysis)
    
    # Output JSON report
    print(json.dumps(report, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
