"""Tests for QA-Manager prompt content (Story 27-01, Story 36-01).

Checks:
1. agents/qa-manager.md contains a tooling-gates checklist item
2. agents/qa-manager.md contains a test-review checklist step
3. agents/qa-manager.md restricts QA test writing to test files only
4. agents/qa-manager.md mentions deriving test strategy from qa_config.json or process.json
5. agents/qa-manager.md verdict schema includes qa_tests_added and qa_review_notes
6. docs/features/_story_template.md Test criteria section mentions QA augmentation

Stdlib only — no external systems, deterministic (repo files are the fixture).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_qa_manager_has_tooling_gates_checklist_item() -> None:
    """agents/qa-manager.md contains a tooling-gates checklist item."""
    qa_manager_path = REPO_ROOT / "agents" / "qa-manager.md"
    assert qa_manager_path.is_file(), f"missing {qa_manager_path.relative_to(REPO_ROOT)}"

    content = qa_manager_path.read_text(encoding="utf-8")

    # Check for tooling gates checklist item (case-insensitive)
    has_tooling_gates = "tooling gate" in content.lower()
    
    assert has_tooling_gates, (
        "qa-manager.md: Checklist missing tooling gates item. "
        "Must include requirement to check '## Tooling Gates' section and verify "
        "lint, typecheck, format, audit gates are configured and passing."
    )


def test_qa_manager_has_test_review_step() -> None:
    """agents/qa-manager.md contains 'test review' in a checklist step."""
    qa_manager_path = REPO_ROOT / "agents" / "qa-manager.md"
    assert qa_manager_path.is_file(), f"missing {qa_manager_path.relative_to(REPO_ROOT)}"

    content = qa_manager_path.read_text(encoding="utf-8")

    # Check for test review in checklist (case-insensitive)
    has_test_review = "test review" in content.lower()
    
    assert has_test_review, (
        "qa-manager.md: Checklist missing test review step. "
        "Must include a step for QA to review developer tests against spec."
    )


def test_qa_manager_augmentation_scope_test_files_only() -> None:
    """agents/qa-manager.md explicitly restricts QA writes to test files (not src/)."""
    qa_manager_path = REPO_ROOT / "agents" / "qa-manager.md"
    assert qa_manager_path.is_file(), f"missing {qa_manager_path.relative_to(REPO_ROOT)}"

    content = qa_manager_path.read_text(encoding="utf-8")

    # Check for explicit restriction on writing to src/ or implementation files
    # Should contain a prohibition like "ONLY test files" and mention src/
    has_scope_restriction = (
        ("src/" in content or "implementation" in content.lower()) and
        ("only test" in content.lower() or "test files" in content.lower() or
         "forbidden" in content.lower())
    )
    
    assert has_scope_restriction, (
        "qa-manager.md: Missing explicit scope restriction on QA test writing. "
        "Must state that QA writes ONLY to test files (tests/*, spec/*, e2e/*, playwright/*, __tests__/*) "
        "and NEVER to src/ or implementation files."
    )


def test_qa_manager_strategy_derived_from_repo_context() -> None:
    """agents/qa-manager.md mentions deriving test strategy from qa_config.json or process.json."""
    qa_manager_path = REPO_ROOT / "agents" / "qa-manager.md"
    assert qa_manager_path.is_file(), f"missing {qa_manager_path.relative_to(REPO_ROOT)}"

    content = qa_manager_path.read_text(encoding="utf-8")

    # Check for mention of qa_config.json or process.json in test strategy context
    has_strategy_context = (
        "qa_config.json" in content or "process.json" in content
    ) and "test strategy" in content.lower()
    
    assert has_strategy_context, (
        "qa-manager.md: Missing reference to deriving test strategy from repo context. "
        "Must mention qa_config.json or process.json in the context of test strategy derivation."
    )


def test_qa_manager_verdict_schema_has_qa_fields() -> None:
    """agents/qa-manager.md verdict JSON schema contains qa_tests_added and qa_review_notes."""
    qa_manager_path = REPO_ROOT / "agents" / "qa-manager.md"
    assert qa_manager_path.is_file(), f"missing {qa_manager_path.relative_to(REPO_ROOT)}"

    content = qa_manager_path.read_text(encoding="utf-8")

    # Check for both qa_tests_added and qa_review_notes in JSON schema
    has_qa_tests_added = "qa_tests_added" in content
    has_qa_review_notes = "qa_review_notes" in content
    
    assert has_qa_tests_added, (
        "qa-manager.md: Verdict JSON schema missing 'qa_tests_added' field. "
        "Must include a list field for test names added by QA."
    )
    
    assert has_qa_review_notes, (
        "qa-manager.md: Verdict JSON schema missing 'qa_review_notes' field. "
        "Must include a string field for QA test review findings."
    )


def test_story_template_has_qa_augmentation_note() -> None:
    """docs/features/_story_template.md Test criteria section mentions QA augmentation."""
    story_template_path = REPO_ROOT / "docs" / "features" / "_story_template.md"
    assert story_template_path.is_file(), f"missing {story_template_path.relative_to(REPO_ROOT)}"

    content = story_template_path.read_text(encoding="utf-8")

    # Check for "QA may augment" in the Test criteria section
    has_qa_augment_note = "qa may augment" in content.lower()
    
    assert has_qa_augment_note, (
        "_story_template.md: Test criteria section missing QA augmentation note. "
        "Must mention that 'QA may augment or correct these criteria during the QA phase.'"
    )
