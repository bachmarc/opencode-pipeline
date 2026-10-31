"""Tests for the architect model-tier policy flip (Story 31-02, F-031).

Checks (repo files are the fixture — stdlib only, deterministic):
1. agents/architect.md states the cheap tier as the architect DEFAULT
   (policy flip: strong tier is no longer the implicit default).
2. agents/architect.md references the escalation points with the exact
   F-030/F-031 strings: ``planning audit``, ``plan_check.py``,
   ``escalate-remedy``, ``BLOCKED_Design``, and the reassignment script
   ``model_assign.py``.
3. agents/architect.md states WHEN the strong planning audit is REQUIRED
   (unresolved plan_check conflicts / new process mechanics) versus
   OPTIONAL (routine replans).
4. agents/architect.md contains the no-discussion prohibition paragraph
   (whitespace-normalized substring match).
5. agents/qa-manager.md contains the tier-trigger paragraph: cheap tier as
   the QA default, three REQUIRED strong points (new-process-mechanics
   first pass / BLOCKED_Design / max_escalations) and the
   ``strong_review_recommended`` flag — with NO concrete model/provider
   names (role abstraction).
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ARCHITECT = REPO_ROOT / "agents" / "architect.md"
QA_MANAGER = REPO_ROOT / "agents" / "qa-manager.md"

# Story 31-02 no-discussion paragraph (verbatim policy text).
NO_DISCUSSION_PARAGRAPH = (
    "Model/provider assignment changes are NEVER discussed, explained, "
    "justified, or recommended. When the user states an assignment, the "
    "architect's entire allowed reaction is: apply via the assignment script "
    "(or acknowledge the user applied it) and confirm the resulting mapping "
    "in ONE line. Suggestions about 'how' or 'where' to put it are prohibited."
)

# Role abstraction: concrete model/provider names are forbidden in portable
# prompts (same patterns as tests/test_framework.py — case-insensitive scan).
FORBIDDEN_MODEL_PATTERNS = (
    "glm-",
    "deepseek",
    "qwen",
    "haiku",
    "claude-",
    "ollama-docker",
    ":cloud",
    "anthropic/",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing {path.relative_to(REPO_ROOT)}"
    return path.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    """Collapse whitespace and strip markdown decoration (backticks, emphasis).

    Underscores are preserved — ``BLOCKED_Design`` and
    ``strong_review_recommended`` must survive normalization intact.
    """
    return " ".join(re.sub(r"[`*]", "", text).split())


def test_cheap_default_stated() -> None:
    """agents/architect.md states the cheap tier as the architect DEFAULT."""
    content = _read(ARCHITECT)

    assert "cheap tier" in content, (
        "architect.md: missing 'cheap tier' — the policy flip must state the "
        "cheap tier as the architect default"
    )
    assert "architect DEFAULT" in content, (
        "architect.md: missing 'architect DEFAULT' statement — the prompt must "
        "name the cheap tier as the default, not the strong tier"
    )


def test_escalation_points_referenced() -> None:
    """agents/architect.md references escalation points with exact strings."""
    content = _read(ARCHITECT)

    for needle in (
        "planning audit",
        "plan_check.py",
        "escalate-remedy",
        "BLOCKED_Design",
        "model_assign.py",
    ):
        assert needle in content, (
            f"architect.md: missing exact string '{needle}' — escalation "
            f"points must use the F-030/F-031 terminology"
        )


def test_planning_audit_trigger_stated() -> None:
    """architect.md states WHEN the strong planning audit is REQUIRED vs OPTIONAL."""
    norm = _normalized(_read(ARCHITECT))

    assert (
        "REQUIRED when plan_check.py reports unresolved conflict candidates "
        "or the feature introduces new process mechanics" in norm
    ), (
        "architect.md: missing REQUIRED triggers for the strong planning "
        "audit (unresolved plan_check conflicts / new process mechanics)"
    )
    assert "OPTIONAL for routine replans" in norm, (
        "architect.md: missing OPTIONAL clause — routine replans stay a "
        "user choice at the planning checkpoint"
    )


def test_no_discussion_rule_present() -> None:
    """architect.md contains the no-discussion prohibition paragraph."""
    norm = _normalized(_read(ARCHITECT))

    assert _normalized(NO_DISCUSSION_PARAGRAPH) in norm, (
        "architect.md: missing the no-discussion prohibition paragraph "
        "(model/provider assignment changes are never discussed, explained, "
        "justified, or recommended)"
    )


def test_qa_tier_triggers_present() -> None:
    """qa-manager.md has tier triggers (cheap default, 3 REQUIRED strong points)."""
    content = _read(QA_MANAGER)
    norm = _normalized(content)

    # Cheap tier is the QA default.
    assert "cheap tier is the QA default" in norm, (
        "qa-manager.md: missing cheap-tier QA default statement"
    )
    # Three REQUIRED strong points (marked mandatory, each named).
    assert "REQUIRED" in content, (
        "qa-manager.md: missing 'REQUIRED' — the strong-tier QA points must "
        "be marked mandatory, not optional"
    )
    assert "new process mechanics" in norm, (
        "qa-manager.md: missing 'new process mechanics' — the FIRST QA pass "
        "of a story introducing new process mechanics requires the strong tier"
    )
    assert "BLOCKED_Design" in content, (
        "qa-manager.md: missing 'BLOCKED_Design' — its diagnosis requires "
        "the strong tier"
    )
    assert "max_escalations" in content, (
        "qa-manager.md: missing 'max_escalations' — escalation budget "
        "exhaustion / breaking-change final gate requires the strong tier"
    )
    # Flag semantics: QA cannot reassign its own model.
    assert "strong_review_recommended" in content, (
        "qa-manager.md: missing 'strong_review_recommended' — verdict flag "
        "for ambiguous criteria / suspected design gaps"
    )
    assert "no-discussion" in norm, (
        "qa-manager.md: tier switch application via the architect must sit "
        "under the same no-discussion rule as model assignment"
    )
    # Role abstraction: no concrete model/provider names in the prompt.
    lowered = content.lower()
    violations = [p for p in FORBIDDEN_MODEL_PATTERNS if p in lowered]
    assert not violations, (
        f"qa-manager.md contains model/provider name patterns: {violations} — "
        f"tier semantics only; concrete models live in the local map"
    )
