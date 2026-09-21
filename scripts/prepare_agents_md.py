#!/usr/bin/env python3
"""AGENTS.md draft generation script.

Combines the template's constant sections with project-specific data extracted
from the analysis JSON (produced by scripts/analyze_project.py).
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_constant_sections(template_content: str) -> dict:
    """Extract the 4 constant sections from the template.
    
    Args:
        template_content: Full template markdown
    
    Returns:
        Dictionary with keys: workflow, git_conventions, languages, prohibitions
    """
    lines = template_content.split("\n")
    
    # Find section start lines
    section_starts = {}
    for i, line in enumerate(lines):
        if line.startswith("## Workflow"):
            section_starts["workflow"] = i
        elif line.startswith("## Languages"):
            section_starts["languages"] = i
        elif line.startswith("## Prohibitions"):
            section_starts["prohibitions"] = i
        elif line.startswith("## References"):
            section_starts["references"] = i
    
    # Extract sections
    sections = {}
    
    # Workflow: from "## Workflow" to "## Languages"
    if "workflow" in section_starts and "languages" in section_starts:
        start = section_starts["workflow"]
        end = section_starts["languages"]
        sections["workflow"] = "\n".join(lines[start:end]).rstrip()
    
    # Languages: from "## Languages" to "## Prohibitions"
    if "languages" in section_starts and "prohibitions" in section_starts:
        start = section_starts["languages"]
        end = section_starts["prohibitions"]
        sections["languages"] = "\n".join(lines[start:end]).rstrip()
    
    # Prohibitions: from "## Prohibitions" to "## References"
    if "prohibitions" in section_starts and "references" in section_starts:
        start = section_starts["prohibitions"]
        end = section_starts["references"]
        sections["prohibitions"] = "\n".join(lines[start:end]).rstrip()
    
    # Git conventions: from "## Git conventions" to "## Workflow"
    git_start = None
    for i, line in enumerate(lines):
        if line.startswith("## Git conventions"):
            git_start = i
            break
    
    if git_start is not None and "workflow" in section_starts:
        start = git_start
        end = section_starts["workflow"]
        sections["git_conventions"] = "\n".join(lines[start:end]).rstrip()
    
    return sections


def get_stack_description(stack: str) -> str:
    """Convert stack type to description."""
    stack_descriptions = {
        "python": "Python 3, pytest",
        "javascript": "JavaScript/Node.js, npm/yarn, Jest",
        "ruby": "Ruby, RSpec",
        "java": "Java, Maven/Gradle, JUnit",
        "mixed": "Multiple languages (see analysis)",
        "unknown": "<TODO: describe stack>",
    }
    return stack_descriptions.get(stack, "<TODO: describe stack>")


def prepare_agents_md(analysis: dict, template_content: str) -> str:
    """Generate AGENTS.md draft from analysis and template.
    
    Args:
        analysis: Dictionary from analyze_project.py
        template_content: Full template markdown
    
    Returns:
        Draft AGENTS.md markdown string
    """
    # Extract constant sections
    constant_sections = extract_constant_sections(template_content)
    
    # Get project name
    project_name = analysis.get("project_name", "unknown-project")
    
    # Get stack
    stack = analysis.get("stack", "unknown")
    stack_desc = get_stack_description(stack)
    
    # Check for src/core and src/adapters
    present_dirs = analysis.get("structure", {}).get("present", [])
    has_core = "src/core" in present_dirs
    has_adapters = "src/adapters" in present_dirs
    
    # Build architecture section
    architecture_section = """## Architecture: function vs connectivity

Strict separation (pattern: `intesis_modbus/CLAUDE.md`):

- **`src/core/`** — pure logic/algorithms.
  - **Zero imports** from framework/IO/HA/DB/API.
  - Receives all data as parameters, returns dicts/primitives.
  - Fully unit-testable, contains simulation helpers (`simulate_<x>()`).
- **`src/adapters/`** — thin wrappers (3-10 lines per method).
  - Extracts request data, **delegates all decisions to core**, returns HTTP response / writes bus.
  - Timers/listeners/schedulers exclusively here.
- **Fakes are mandatory** for every external dependency: `tests/fakes/`.
  - Core tests run **without** real systems (`FakeClock`, `Fake<X>` interfaces).
  - **Fake = same method signatures as the real adapter.** Fakes offering a different
    interface than the adapter → design error. The real orchestration code must
    be callable with fakes, without modifications.
  - If core is not testable without fakes → design error.
- **Integration tests test the real orchestration code** (e.g. `Scheduler._run_cycle()`
  with fakes), not a manual reconstruction of the cycle. Manually reconstructed cycles bypass
  wiring bugs and are worthless as integration proof."""
    
    # Build references section
    references_lines = ["## References", ""]
    references_lines.append("- `docs/requirements.md` — Documenter-generated feature overview (derived summary)")
    references_lines.append("- `docs/design.md` — Documenter-generated architecture summary (derived)")
    references_lines.append("- `STORIES.md` — story index (status per story)")
    
    # Add detected doc files
    if "docs/features" in present_dirs:
        references_lines.append("- `docs/features/` — feature specifications")
    
    references_section = "\n".join(references_lines)
    
    # Build core rules section
    core_rules_lines = ["## Core rules (project source of truth: feature files + story files)", ""]
    core_rules_lines.append("- <TODO: core rule 1>")
    core_rules_lines.append("- <TODO: core rule 2>")
    core_rules_lines.append("- <… more, taken from `docs/design.md` § core decisions>")
    core_rules_lines.append("- **Fake requirement:** For EVERY external dependency (`<API>`, `<DB>`, `<HA>`, …) there exists a fake in `tests/fakes/` — tests run without real systems.")
    core_rules_section = "\n".join(core_rules_lines)
    
    # Build the full output
    output_lines = []
    
    # Title
    output_lines.append(f"# AGENTS.md — {project_name}")
    output_lines.append("")
    
    # Intro
    output_lines.append("> Skeleton from the opencode pipeline (`templates/AGENTS.md`). Fill in: everything in `<...>`.")
    output_lines.append("> Constant sections (Workflow, Git, Languages, Prohibitions) **must not** be modified per project —")
    output_lines.append("> they are the binding interface between framework and project.")
    output_lines.append("> Project-specific: project name, stack, core rules, references (§ \"This project\").")
    output_lines.append("")
    
    # This project section
    output_lines.append(f"## This project: <Name, one-liner>")
    output_lines.append("")
    output_lines.append("- **What:** <TODO: describe what this project does, target audience, scope>")
    output_lines.append(f"- **Stack:** {stack_desc}")
    output_lines.append("- **Versioning:** `APP_VERSION = \"0.1.0\"` (in `src/<version>.py` or similar) — bump on every merge")
    output_lines.append("")
    
    # Core rules
    output_lines.append(core_rules_section)
    output_lines.append("")
    
    # Architecture
    output_lines.append(architecture_section)
    output_lines.append("")
    
    # Git conventions (constant)
    output_lines.append(constant_sections.get("git_conventions", ""))
    output_lines.append("")
    
    # Workflow (constant)
    output_lines.append(constant_sections.get("workflow", ""))
    output_lines.append("")
    
    # Languages (constant)
    output_lines.append(constant_sections.get("languages", ""))
    output_lines.append("")
    
    # Prohibitions (constant)
    output_lines.append(constant_sections.get("prohibitions", ""))
    output_lines.append("")
    
    # References
    output_lines.append(references_section)
    output_lines.append("")
    
    # Append existing content if present
    agent_file = analysis.get("agent_file", {})
    if agent_file.get("type") != "none" and agent_file.get("content"):
        output_lines.append("<!-- EXISTING AGENT FILE CONTENT (review and extract project-specific information) -->")
        output_lines.append(agent_file["content"])
        output_lines.append("<!-- END EXISTING CONTENT -->")
    
    return "\n".join(output_lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate AGENTS.md draft from project analysis"
    )
    parser.add_argument(
        "analysis_file",
        help="Path to analysis JSON file (from analyze_project.py)"
    )
    parser.add_argument(
        "--template",
        help="Path to template file (default: templates/AGENTS.md relative to script)",
        default=None
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: stdout)",
        default=None
    )
    
    args = parser.parse_args()
    
    # Resolve analysis file
    analysis_path = Path(args.analysis_file).resolve()
    if not analysis_path.exists():
        sys.exit(1)
    
    # Resolve template file
    if args.template:
        template_path = Path(args.template).resolve()
    else:
        # Default: templates/AGENTS.md relative to script's parent directory
        template_path = Path(__file__).parent.parent / "templates" / "AGENTS.md"
    
    if not template_path.exists():
        sys.exit(2)
    
    # Read files
    # Try to detect encoding
    try:
        with open(analysis_path, encoding="utf-8-sig") as f:
            analysis = json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError):
        # Try UTF-16
        with open(analysis_path, encoding="utf-16") as f:
            analysis = json.load(f)
    
    with open(template_path, encoding="utf-8") as f:
        template_content = f.read()
    
    # Generate draft
    draft = prepare_agents_md(analysis, template_content)
    
    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(draft, encoding="utf-8")
    else:
        print(draft)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
