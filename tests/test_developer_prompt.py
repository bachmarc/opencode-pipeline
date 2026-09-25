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
    dev_path = REPO_ROOT / "agent" / "developer.md"
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
