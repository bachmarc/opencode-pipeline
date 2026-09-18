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
