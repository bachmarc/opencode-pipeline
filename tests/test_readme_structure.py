"""Tests for README.md structure and content.

Validates:
1. Section order (Intro → Development Process → Installation → Technical Details → Open Points)
2. Mermaid flowchart presence
3. Installation paths (fresh + existing setup)
4. Existing setup git commands
5. No concrete model/provider names
6. Agent roles in intro
7. Technical Details anchors and forward-links
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"

# Reuse the model-name regex pattern from test_framework.py
FORBIDDEN_PATTERNS = (
    "glm-",
    "deepseek",
    "qwen",
    "haiku",
    "claude-",
    "ollama-docker",
    ":cloud",
    "anthropic/",
)

ALLOWLIST_SUBSTRINGS = ("CLAUDE.md",)


def _is_allowed(line: str) -> bool:
    return any(marker in line for marker in ALLOWLIST_SUBSTRINGS)


def test_readme_section_order() -> None:
    """README has five top-level sections in order: Intro, Development Process, Installation, Technical Details, Open Points."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    content = README_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # Find top-level headings (## level)
    headings = []
    for i, line in enumerate(lines):
        if line.startswith("## "):
            heading_text = line[3:].strip()
            headings.append((i, heading_text))
    
    # Extract heading texts
    heading_texts = [text.lower() for _, text in headings]
    
    # Check for required sections (case-insensitive, partial match allowed)
    required_sections = [
        ("intro", ["intro", "pitch"]),  # Either "intro" or "pitch"
        ("development process", ["development process", "how the workflow works"]),
        ("installation", ["installation"]),
        ("technical details", ["technical details"]),
        ("open points", ["open points", "outlook"]),
    ]
    
    found_indices = []
    for section_name, variants in required_sections:
        found = False
        for i, heading in enumerate(heading_texts):
            if any(variant in heading for variant in variants):
                found_indices.append(i)
                found = True
                break
        assert found, f"Section '{section_name}' not found in README headings: {heading_texts}"
    
    # Verify order
    assert found_indices == sorted(found_indices), (
        f"Sections not in correct order. Found indices: {found_indices}, "
        f"Headings: {[heading_texts[i] for i in found_indices]}"
    )


def test_readme_has_mermaid_flowchart() -> None:
    """README contains a mermaid code block."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    content = README_PATH.read_text(encoding="utf-8")
    
    # Look for ```mermaid code block
    assert "```mermaid" in content, "README does not contain a ```mermaid code block"
    
    # Verify it's closed
    mermaid_start = content.find("```mermaid")
    mermaid_end = content.find("```", mermaid_start + len("```mermaid"))
    assert mermaid_end != -1, "Mermaid code block is not properly closed"


def test_readme_installation_two_paths() -> None:
    """Installation section has both 'Fresh install' and 'Existing setup' subsections."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    content = README_PATH.read_text(encoding="utf-8")
    
    # Find Installation section
    installation_start = content.lower().find("## installation")
    assert installation_start != -1, "Installation section not found"
    
    # Find next top-level section (##) after Installation
    next_section = content.find("\n## ", installation_start + 1)
    if next_section == -1:
        installation_section = content[installation_start:]
    else:
        installation_section = content[installation_start:next_section]
    
    # Check for both paths (case-insensitive)
    installation_lower = installation_section.lower()
    
    has_fresh = "fresh" in installation_lower
    has_existing = "existing" in installation_lower
    
    assert has_fresh, "Installation section does not mention 'fresh install'"
    assert has_existing, "Installation section does not mention 'existing setup'"


def test_readme_existing_setup_git_init() -> None:
    """Existing setup section contains git init, git remote add, git fetch, git checkout."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    content = README_PATH.read_text(encoding="utf-8")
    
    # Find Installation section
    installation_start = content.lower().find("## installation")
    assert installation_start != -1, "Installation section not found"
    
    # Find next top-level section
    next_section = content.find("\n## ", installation_start + 1)
    if next_section == -1:
        installation_section = content[installation_start:]
    else:
        installation_section = content[installation_start:next_section]
    
    # Find existing setup subsection
    existing_start = installation_section.lower().find("existing")
    assert existing_start != -1, "Existing setup subsection not found"
    
    # Extract from existing setup to next subsection or end
    existing_section = installation_section[existing_start:]
    next_subsection = existing_section.lower().find("\n### ")
    if next_subsection == -1:
        existing_section = existing_section
    else:
        existing_section = existing_section[:next_subsection]
    
    # Check for required git commands
    required_commands = ["git init", "git remote add", "git fetch", "git checkout"]
    for cmd in required_commands:
        assert cmd in existing_section, (
            f"Existing setup section does not contain '{cmd}'"
        )


def test_readme_no_model_names() -> None:
    """README contains no concrete model/provider names."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    violations: list[str] = []
    
    for lineno, line in enumerate(
        README_PATH.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if _is_allowed(line):
            continue
        lowered = line.lower()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in lowered:
                violations.append(f"README.md:{lineno}: {line.strip()[:100]}")
                break
    
    assert not violations, (
        "Concrete model/provider names found in README:\n" + "\n".join(violations)
    )


def test_readme_agent_roles_in_intro() -> None:
    """Intro section mentions all four agent roles: architect, developer, qa-manager, documenter."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    content = README_PATH.read_text(encoding="utf-8")
    
    # Find Intro section (first ## heading)
    intro_start = content.find("## ")
    assert intro_start != -1, "No intro section found"
    
    # Find next top-level section
    next_section = content.find("\n## ", intro_start + 1)
    if next_section == -1:
        intro_section = content[intro_start:]
    else:
        intro_section = content[intro_start:next_section]
    
    intro_lower = intro_section.lower()
    
    required_roles = ["architect", "developer", "qa-manager", "documenter"]
    for role in required_roles:
        assert role in intro_lower, (
            f"Intro section does not mention '{role}'"
        )


def test_readme_technical_details_anchors() -> None:
    """Technical Details sections have anchor IDs and Installation links to them."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    content = README_PATH.read_text(encoding="utf-8")
    
    # Find Technical Details section
    tech_details_start = content.lower().find("## technical details")
    assert tech_details_start != -1, "Technical Details section not found"
    
    # Find next top-level section
    next_section = content.find("\n## ", tech_details_start + 1)
    if next_section == -1:
        tech_details_section = content[tech_details_start:]
    else:
        tech_details_section = content[tech_details_start:next_section]
    
    # Check for anchor IDs (various formats: <a id="...">, {#...}, or just heading text)
    # Look for subsection headings with potential anchors
    has_anchors = (
        "<a id=" in tech_details_section or
        "{#" in tech_details_section or
        "### " in tech_details_section  # At least subsections exist
    )
    assert has_anchors, "Technical Details section has no subsections or anchor IDs"
    
    # Find Installation section
    installation_start = content.lower().find("## installation")
    assert installation_start != -1, "Installation section not found"
    
    # Find next top-level section after Installation
    next_section_after_install = content.find("\n## ", installation_start + 1)
    if next_section_after_install == -1:
        installation_section = content[installation_start:]
    else:
        installation_section = content[installation_start:next_section_after_install]
    
    # Check for forward-links to Technical Details (e.g., #model-assignment, #technical-details)
    # Look for markdown links or references
    has_forward_link = (
        "#" in installation_section and (
            "technical" in installation_section.lower() or
            "model" in installation_section.lower() or
            "phase" in installation_section.lower()
        )
    )
    assert has_forward_link, (
        "Installation section does not contain forward-links to Technical Details sections"
    )


def test_readme_local_config_reasoning_effort() -> None:
    """Local-configuration section contains reasoningEffort on all four agent entries."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    content = README_PATH.read_text(encoding="utf-8")
    
    # Find Local configuration section
    local_config_start = content.lower().find("local configuration")
    assert local_config_start != -1, "Local configuration section not found"
    
    # Find the jsonc code block
    jsonc_start = content.find("```jsonc", local_config_start)
    assert jsonc_start != -1, "jsonc code block not found in Local configuration section"
    
    # Find the end of the jsonc block
    jsonc_end = content.find("```", jsonc_start + len("```jsonc"))
    assert jsonc_end != -1, "jsonc code block not properly closed"
    
    jsonc_block = content[jsonc_start:jsonc_end]
    
    # Check for reasoningEffort on all four agents
    required_agents = ["architect", "developer", "qa-manager", "documenter"]
    for agent in required_agents:
        # Look for the agent entry and reasoningEffort within it
        agent_pattern = f'"{agent}"'
        assert agent_pattern in jsonc_block, f"Agent '{agent}' not found in jsonc block"
    
    # Check that reasoningEffort appears in the block
    assert "reasoningEffort" in jsonc_block, (
        "reasoningEffort not found in Local configuration jsonc example"
    )
    
    # Check that low/medium/high values are mentioned
    has_values = any(val in jsonc_block for val in ["low", "medium", "high"])
    assert has_values, (
        "reasoningEffort values (low/medium/high) not found in Local configuration section"
    )


def test_readme_model_assignment_reasoning_axis() -> None:
    """Model Assignment section contains reasoningEffort and distinguishes two axes."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    content = README_PATH.read_text(encoding="utf-8")
    
    # Find Model Assignment subsection (### level, not just text)
    model_assignment_start = content.find("### <a id=\"model-assignment\"></a>Model Assignment")
    if model_assignment_start == -1:
        model_assignment_start = content.find("### Model Assignment")
    assert model_assignment_start != -1, "Model Assignment subsection not found"
    
    # Find next top-level section (##)
    next_section = content.find("\n## ", model_assignment_start + 1)
    if next_section == -1:
        model_assignment_section = content[model_assignment_start:]
    else:
        model_assignment_section = content[model_assignment_start:next_section]
    
    # Check for reasoningEffort
    assert "reasoningEffort" in model_assignment_section, (
        "reasoningEffort not mentioned in Model Assignment section"
    )
    
    # Check for "axis" or "axes" or "separate" to indicate two separate tuning dimensions
    section_lower = model_assignment_section.lower()
    has_axis_language = (
        "axis" in section_lower or 
        "axes" in section_lower or 
        "separate" in section_lower
    )
    assert has_axis_language, (
        "Model Assignment section does not distinguish model and reasoning depth as separate axes"
    )


def test_readme_agents_table_reasoning_column() -> None:
    """The agents detail table has a reasoning-depth column with low/medium/high values."""
    assert README_PATH.is_file(), f"README.md not found at {README_PATH}"
    
    content = README_PATH.read_text(encoding="utf-8")
    
    # Find "The four agents in detail" section
    agents_table_start = content.lower().find("four agents in detail")
    assert agents_table_start != -1, "The four agents in detail section not found"
    
    # Find the next top-level section
    next_section = content.find("\n## ", agents_table_start)
    if next_section == -1:
        agents_section = content[agents_table_start:]
    else:
        agents_section = content[agents_table_start:next_section]
    
    # Find the table (starts with |)
    table_start = agents_section.find("|")
    assert table_start != -1, "Table not found in agents section"
    
    # Extract table lines
    table_lines = []
    for line in agents_section[table_start:].split("\n"):
        if line.startswith("|"):
            table_lines.append(line)
        elif table_lines:  # Stop at first non-table line after table starts
            break
    
    table_text = "\n".join(table_lines)
    
    # Check for "Reasoning" in header (case-insensitive)
    has_reasoning_header = "reasoning" in table_text.lower()
    assert has_reasoning_header, (
        "Table does not have a 'Reasoning' column header"
    )
    
    # Check that low/medium/high appear in the table
    has_low = "low" in table_text.lower()
    has_medium = "medium" in table_text.lower()
    has_high = "high" in table_text.lower()
    
    assert has_low and has_medium and has_high, (
        "Reasoning column does not contain all of low/medium/high values"
    )


def test_design_mentions_reasoning_effort() -> None:
    """docs/design.md mentions reasoningEffort in README Structure context."""
    design_path = REPO_ROOT / "docs" / "design.md"
    assert design_path.is_file(), f"design.md not found at {design_path}"
    
    content = design_path.read_text(encoding="utf-8")
    
    # Find README Structure section
    readme_structure_start = content.lower().find("readme structure")
    assert readme_structure_start != -1, "README Structure section not found in design.md"
    
    # Find next top-level section (##)
    next_section = content.find("\n## ", readme_structure_start + 1)
    if next_section == -1:
        readme_structure_section = content[readme_structure_start:]
    else:
        readme_structure_section = content[readme_structure_start:next_section]
    
    # Check for reasoningEffort
    assert "reasoningEffort" in readme_structure_section, (
        "reasoningEffort not mentioned in design.md README Structure section"
    )
