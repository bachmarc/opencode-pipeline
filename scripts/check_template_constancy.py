#!/usr/bin/env python3
"""Check template constancy between templates/AGENTS.md and project AGENTS.md.

Extracts constant sections (Workflow, Git conventions, Languages, Prohibitions)
from both files and compares them.

Exit codes:
  0 - PASS: sections are identical
  1 - FAIL: sections differ
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


CONSTANT_SECTIONS = [
    "## Workflow",
    "## Git conventions",
    "## Languages",
    "## Prohibitions",
]


def extract_sections(content: str) -> Dict[str, str]:
    """Extract constant sections from markdown content.
    
    Returns a dict mapping section name to section content (including heading).
    """
    sections = {}
    lines = content.split('\n')
    
    for section_heading in CONSTANT_SECTIONS:
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
    """Normalize text by stripping leading/trailing whitespace per line."""
    return [line.rstrip() for line in text.split('\n')]


def compare_sections(template_sections: Dict[str, str], 
                    project_sections: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Compare sections between template and project.
    
    Returns (is_identical, list_of_different_sections).
    """
    different_sections = []
    
    for section_name in CONSTANT_SECTIONS:
        section_key = section_name.replace("## ", "")
        
        template_content = template_sections.get(section_key, "")
        project_content = project_sections.get(section_key, "")
        
        template_lines = normalize_lines(template_content)
        project_lines = normalize_lines(project_content)
        
        if template_lines != project_lines:
            different_sections.append(section_key)
    
    is_identical = len(different_sections) == 0
    return is_identical, different_sections


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "result": "FAIL",
            "error": "Usage: check_template_constancy.py <project-agents-md>"
        }))
        sys.exit(1)
    
    project_agents_path = Path(sys.argv[1])
    
    if not project_agents_path.exists():
        print(json.dumps({
            "result": "FAIL",
            "error": f"Project AGENTS.md not found: {project_agents_path}"
        }))
        sys.exit(1)
    
    # Find templates/AGENTS.md relative to this script
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    template_path = repo_root / "templates" / "AGENTS.md"
    
    if not template_path.exists():
        print(json.dumps({
            "result": "FAIL",
            "error": f"Template AGENTS.md not found: {template_path}"
        }))
        sys.exit(1)
    
    # Read both files
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        with open(project_agents_path, 'r', encoding='utf-8') as f:
            project_content = f.read()
    except Exception as e:
        print(json.dumps({
            "result": "FAIL",
            "error": f"Error reading files: {e}"
        }))
        sys.exit(1)
    
    # Extract sections
    template_sections = extract_sections(template_content)
    project_sections = extract_sections(project_content)
    
    # Compare
    is_identical, different_sections = compare_sections(template_sections, project_sections)
    
    if is_identical:
        print(json.dumps({"result": "PASS"}))
        sys.exit(0)
    else:
        print(json.dumps({
            "result": "FAIL",
            "sections": different_sections,
            "diff": f"Sections differ: {', '.join(different_sections)}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
