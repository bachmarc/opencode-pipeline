"""Tests for QA-Manager prompt content (Story 27-01).

Checks:
1. agents/qa-manager.md contains a tooling-gates checklist item

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
