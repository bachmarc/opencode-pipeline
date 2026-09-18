"""
Tests for orchestration rules enforcement (Story 06-14).

These tests verify that:
1. Architect prompt contains Phase 3 Orchestration section with all 4 rules
2. QA-Manager prompt contains single-story enforcement rule
3. Design documentation includes orchestration principles
4. No concrete model/provider names are introduced
"""

import re
from pathlib import Path


def test_architect_has_orchestration_section():
    """Architect.md contains 'Phase 3 Orchestration' section."""
    architect_path = Path(__file__).parent.parent / "agent" / "architect.md"
    content = architect_path.read_text(encoding="utf-8")
    assert "## Phase 3 Orchestration" in content, \
        "architect.md missing '## Phase 3 Orchestration' section"


def test_architect_no_batch_qa_rule():
    """Architect.md contains 'Do NOT batch' rule."""
    architect_path = Path(__file__).parent.parent / "agent" / "architect.md"
    content = architect_path.read_text(encoding="utf-8")
    assert "Do NOT batch" in content, \
        "architect.md missing 'Do NOT batch' rule"


def test_architect_no_own_pytest_rule():
    """Architect.md contains 'Do NOT run pytest yourself' rule."""
    architect_path = Path(__file__).parent.parent / "agent" / "architect.md"
    content = architect_path.read_text(encoding="utf-8")
    assert "Do NOT run pytest yourself" in content, \
        "architect.md missing 'Do NOT run pytest yourself' rule"


def test_qa_single_story_enforcement():
    """QA-Manager.md contains single-story enforcement rule."""
    qa_manager_path = Path(__file__).parent.parent / "agent" / "qa-manager.md"
    content = qa_manager_path.read_text(encoding="utf-8")
    assert "Single-story enforcement" in content, \
        "qa-manager.md missing 'Single-story enforcement' rule"
    assert "Batch-QA forbidden" in content, \
        "qa-manager.md missing 'Batch-QA forbidden' text"


def test_design_orchestration_section():
    """Design.md contains 'Orchestration principles' section."""
    design_path = Path(__file__).parent.parent / "docs" / "design.md"
    content = design_path.read_text(encoding="utf-8")
    assert "## 14. Orchestration principles" in content, \
        "design.md missing '## 14. Orchestration principles' section"


def test_no_model_names():
    """No concrete model/provider names introduced in changed files."""
    # Known model/provider patterns to check
    model_patterns = [
        r"claude-\d+",  # claude-3, claude-opus, etc.
        r"gpt-\d+",     # gpt-4, gpt-3.5, etc.
        r"glm-\d+",     # GLM models
        r"deepseek",    # DeepSeek
        r"qwen",        # Qwen
        r"haiku",       # Haiku (unless in legitimate context)
        r"ollama-docker",  # Ollama
        r":cloud",      # Cloud provider suffix
    ]
    
    # Check only the new sections added by this story
    architect_path = Path(__file__).parent.parent / "agent" / "architect.md"
    architect_content = architect_path.read_text(encoding="utf-8")
    # Extract only the Phase 3 Orchestration section
    if "## Phase 3 Orchestration" in architect_content:
        phase3_start = architect_content.find("## Phase 3 Orchestration")
        phase3_end = architect_content.find("## Merge Discipline", phase3_start)
        phase3_section = architect_content[phase3_start:phase3_end]
        
        for pattern in model_patterns:
            matches = re.finditer(pattern, phase3_section, re.IGNORECASE)
            for match in matches:
                match_text = match.group()
                assert False, \
                    f"Concrete model name '{match_text}' found in Phase 3 Orchestration section"
    
    # Check QA-Manager single-story enforcement section
    qa_manager_path = Path(__file__).parent.parent / "agent" / "qa-manager.md"
    qa_manager_content = qa_manager_path.read_text(encoding="utf-8")
    if "Single-story enforcement" in qa_manager_content:
        enforcement_start = qa_manager_content.find("**Single-story enforcement:**")
        enforcement_end = qa_manager_content.find("## Checklist", enforcement_start)
        enforcement_section = qa_manager_content[enforcement_start:enforcement_end]
        
        for pattern in model_patterns:
            matches = re.finditer(pattern, enforcement_section, re.IGNORECASE)
            for match in matches:
                match_text = match.group()
                assert False, \
                    f"Concrete model name '{match_text}' found in Single-story enforcement section"
    
    # Check design.md orchestration principles section
    design_path = Path(__file__).parent.parent / "docs" / "design.md"
    design_content = design_path.read_text(encoding="utf-8")
    if "## 14. Orchestration principles" in design_content:
        orch_start = design_content.find("## 14. Orchestration principles")
        orch_section = design_content[orch_start:]  # to end of file
        
        for pattern in model_patterns:
            matches = re.finditer(pattern, orch_section, re.IGNORECASE)
            for match in matches:
                match_text = match.group()
                assert False, \
                    f"Concrete model name '{match_text}' found in Orchestration principles section"
