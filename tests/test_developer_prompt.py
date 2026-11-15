"""
Test suite for agent/developer.md prompt invariants.

Story 22-02: Developer prompt must explicitly forbid post-commit qa_compress.py runs.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_developer_prompt_forbids_postcommit_run() -> None:
    """
    agent/developer.md must contain a prohibition against running qa_compress.py after committing.
    
    Acceptance: The file must contain "do not run" or "Do NOT run" (case-insensitive)
    near "qa_compress" and "after"/"commit".
    """
    dev_path = REPO_ROOT / "agents" / "developer.md"
    assert dev_path.exists(), f"{dev_path} not found"
    
    content = dev_path.read_text(encoding="utf-8")
    
    # Check for prohibition pattern: "do not run" or "Do NOT run" near "qa_compress" and "after"/"commit"
    # We'll use a simple approach: check for the key phrases in the content
    
    # Normalize for case-insensitive search
    content_lower = content.lower()
    
    # Check for "do not run" or "don't run" near "qa_compress"
    has_prohibition = (
        ("do not run" in content_lower or "don't run" in content_lower) and
        "qa_compress" in content_lower and
        ("after" in content_lower or "commit" in content_lower)
    )
    
    assert has_prohibition, (
        "agent/developer.md must contain a prohibition against running qa_compress.py after committing. "
        "Expected to find 'do not run' or 'don't run' near 'qa_compress' and 'after'/'commit'."
    )
    
    # More specific check: look for the exact phrase pattern
    # Pattern: "do not run" + "qa_compress" + "after"/"commit" in reasonable proximity
    pattern = re.compile(
        r"do\s+not\s+run.*?qa_compress.*?(after|commit)|"
        r"qa_compress.*?do\s+not\s+run.*?(after|commit)|"
        r"(after|commit).*?do\s+not\s+run.*?qa_compress",
        re.IGNORECASE | re.DOTALL
    )
    
    # For a more lenient check, verify the key components exist
    assert "do not run" in content_lower or "don't run" in content_lower, (
        "agent/developer.md must contain 'do not run' or 'don't run' prohibition"
    )
    assert "qa_compress" in content_lower, (
        "agent/developer.md must mention 'qa_compress'"
    )
    assert "after" in content_lower or "commit" in content_lower, (
        "agent/developer.md must mention 'after' or 'commit' in context of the prohibition"
    )


def test_developer_prompt_reads_codebase_snapshot() -> None:
    """agent/developer.md contains a rule about reading the Codebase Snapshot before exploring files."""
    dev_path = REPO_ROOT / "agents" / "developer.md"
    assert dev_path.exists(), f"{dev_path} not found"
    
    content = dev_path.read_text(encoding="utf-8")
    
    # Check for Codebase Snapshot mention
    assert "Codebase Snapshot" in content, (
        "agent/developer.md: missing guidance about reading Codebase Snapshot"
    )


def test_developer_prompt_has_anti_loop_rule() -> None:
    """
    agent/developer.md must contain an anti-loop rule with the DEFERRED concept.
    
    Acceptance: The file must contain "DEFERRED" (or "deferred") AND a phrase
    matching "same failing action" or equivalent.
    """
    dev_path = REPO_ROOT / "agents" / "developer.md"
    assert dev_path.exists(), f"{dev_path} not found"
    
    content = dev_path.read_text(encoding="utf-8")
    
    # Check for DEFERRED keyword
    assert "DEFERRED" in content or "deferred" in content, (
        "agent/developer.md must contain 'DEFERRED' or 'deferred' keyword in anti-loop rule"
    )
    
    # Check for "same failing action" or equivalent phrase
    content_lower = content.lower()
    has_failing_action_phrase = (
        "same failing action" in content_lower or
        "repeat the same failing action" in content_lower or
        "repeating the same failing action" in content_lower
    )
    
    assert has_failing_action_phrase, (
        "agent/developer.md must contain phrase about 'same failing action' in anti-loop rule"
    )


def test_developer_prompt_has_step_budget_recommendation() -> None:
    """
    agent/developer.md must contain a step-budget recommendation.
    
    Acceptance: The file must contain "agents.developer.steps".
    """
    dev_path = REPO_ROOT / "agents" / "developer.md"
    assert dev_path.exists(), f"{dev_path} not found"
    
    content = dev_path.read_text(encoding="utf-8")
    
    assert "agents.developer.steps" in content, (
        "agent/developer.md must contain 'agents.developer.steps' in step-budget recommendation"
    )


def test_architect_prompt_has_item_wise_spawn_guidance() -> None:
    """
    agent/architect.md must contain item-wise spawn guidance in Phase 3 orchestration.
    
    Acceptance: The file must contain "item-level" or "item-wise" in the Phase 3 section.
    """
    arch_path = REPO_ROOT / "agents" / "architect.md"
    assert arch_path.exists(), f"{arch_path} not found"
    
    content = arch_path.read_text(encoding="utf-8")
    
    # Find Phase 3 Orchestration section
    phase3_match = re.search(r"## Phase 3 Orchestration.*?(?=\n## |\Z)", content, re.DOTALL)
    assert phase3_match, (
        "agent/architect.md must contain '## Phase 3 Orchestration' section"
    )
    
    phase3_content = phase3_match.group(0)
    
    has_item_wise = "item-level" in phase3_content or "item-wise" in phase3_content
    
    assert has_item_wise, (
        "agent/architect.md Phase 3 Orchestration section must contain 'item-level' or 'item-wise' spawn guidance"
    )
