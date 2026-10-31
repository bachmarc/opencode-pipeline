"""Prompt self-checks for Story 32-01 (F-032): boundary checklist, ordering
invariants, bugfix completeness.

VirtOffice retrospective: the largest bug clusters were lifecycle ordering
and underspecified boundary behavior — planning gaps, not coding mistakes.
This story makes the boundary checklist and the Ordering & Recovery
Invariants section part of the planning vocabulary, and turns regression
nets into a QA rule. Repo files are the fixture (stdlib only, deterministic
— same pattern as tests/test_architect_model_policy.py). Pins:

1. agents/architect.md carries the boundary checklist with the five
   verbatim questions (degenerate/empty inputs, intermediate states,
   abort/error semantics mid-flight, repeat/reconnect idempotency,
   environment matrix).
2. agents/architect.md carries the marker-generation rule: unclear or
   undecided answers MUST become ``[NEEDS CLARIFICATION`` markers in the
   story (plan_check enforces resolution before dev starts) — plus the
   lifecycle invariant-section rule.
3. agents/qa-manager.md carries the bugfix-completeness rule (PASS only
   with a regression test that would have caught the fixed bug, provenance
   ``tier-k``) and the invariant-section FAIL rule.
4. docs/features/_story_template.md carries ONE commented section hint
   (``## Ordering & Recovery Invariants (mandatory for lifecycle stories)``)
   inside the Test criteria area. The hint is an HTML comment — it persists
   verbatim into generated stories, so it must NOT contain a literal
   ``[NEEDS CLARIFICATION`` marker (plan_check scans story files line-wise
   and would flag every generated story).
5. Template constancy vs main (branch base): the pre-existing template
   content survives byte-identical and in order — the edit is
   additions-only, so constant sections and the debug-type comment block
   stay intact.
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

ARCHITECT = REPO_ROOT / "agents" / "architect.md"
QA_MANAGER = REPO_ROOT / "agents" / "qa-manager.md"
TEMPLATE = REPO_ROOT / "docs" / "features" / "_story_template.md"

# The five generic boundary questions — verbatim per Story 32-01.
BOUNDARY_QUESTIONS = (
    "What happens on degenerate/empty inputs or states?",
    "What is visible in intermediate states during transitions?",
    "What is the abort/error semantics mid-flight (stop, rollback)?",
    "What happens on repeat/reconnect — is it idempotent?",
    "Which environments does it run in (and which combination matters)?",
)

# The exact commented section hint (heading line inside an HTML comment).
INVARIANT_HEADING = "## Ordering & Recovery Invariants (mandatory for lifecycle stories)"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing {path.relative_to(REPO_ROOT)}"
    return path.read_text(encoding="utf-8")


def _template_blob_at_branch_base() -> bytes | None:
    """Template bytes at the branch base (merge-base HEAD main).

    Returns None when git or the main branch is unavailable — the constancy
    test then skips instead of failing for environmental reasons.
    """
    try:
        base = subprocess.run(
            ["git", "merge-base", "HEAD", "main"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        result = subprocess.run(
            ["git", "show", f"{base}:docs/features/_story_template.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout


# --- (a) boundary checklist in architect.md ---------------------------------


def test_five_boundary_questions_verbatim() -> None:
    """architect.md carries the five boundary questions verbatim."""
    content = _read(ARCHITECT)

    for question in BOUNDARY_QUESTIONS:
        assert question in content, (
            f"architect.md: missing verbatim boundary question {question!r} — "
            f"the checklist must list all five questions word-for-word"
        )


def test_boundary_checklist_is_design_phase_guidance() -> None:
    """architect.md names the checklist as design-phase guidance."""
    content = _read(ARCHITECT).lower()

    assert "boundary checklist" in content, (
        "architect.md: missing 'boundary checklist' — the five questions must "
        "be introduced as a named design-phase checklist, not scattered prose"
    )


# --- (b) marker-generation rule in architect.md -----------------------------


def test_marker_generation_rule_present() -> None:
    """architect.md: unclear boundary answers MUST become clarification markers."""
    content = _read(ARCHITECT)

    assert "[NEEDS CLARIFICATION" in content, (
        "architect.md: missing '[NEEDS CLARIFICATION' — the marker-generation "
        "rule must reference the exact marker syntax"
    )
    assert "MUST become" in content, (
        "architect.md: missing 'MUST become' — unclear or undecided answers "
        "are mandatory marker material, not optional annotations"
    )
    normalized = " ".join(content.lower().split())
    assert "unclear or undecided" in normalized, (
        "architect.md: missing 'unclear or undecided' — the rule must cover "
        "both unclear answers and consciously postponed decisions"
    )


# --- (c) bugfix-completeness rule in qa-manager.md --------------------------


def test_bugfix_completeness_rule_present() -> None:
    """qa-manager.md: bugfix PASS requires a catching regression test (tier-k)."""
    content = _read(QA_MANAGER)

    assert "regression test" in content, (
        "qa-manager.md: missing 'regression test' — the bugfix-completeness "
        "rule must demand a regression net"
    )
    assert "would have caught" in content, (
        "qa-manager.md: missing 'would have caught' — the regression test must "
        "be a repro of the failure, proven by counterfactual wording"
    )
    assert "tier-k" in content, (
        "qa-manager.md: missing 'tier-k' — judging whether a regression test "
        "would have caught the bug is an LLM judgment, not a Tier D script"
    )
    normalized = " ".join(content.lower().split())
    assert "bugfix story is pass only if" in normalized, (
        "qa-manager.md: missing 'bugfix story is PASS only if' — the rule must "
        "gate PASS, not merely recommend a regression test"
    )


# --- (c) invariant-section FAIL rule in qa-manager.md -----------------------


def test_invariant_section_fail_rule_present() -> None:
    """qa-manager.md: missing invariants section on lifecycle stories = FAIL."""
    content = _read(QA_MANAGER)

    assert "Ordering & Recovery Invariants" in content, (
        "qa-manager.md: missing 'Ordering & Recovery Invariants' — the QA rule "
        "must name the section exactly as the template hint does"
    )
    normalized = " ".join(content.lower().split())
    assert "must exist and be tested" in normalized, (
        "qa-manager.md: missing 'must exist and be tested' — the section must "
        "not only exist but be covered by tests"
    )
    assert "missing" in normalized and "fail" in normalized, (
        "qa-manager.md: missing 'missing -> FAIL' — a missing invariants "
        "section is a FAIL verdict, not BLOCKED (the template hint names it)"
    )


# --- (d) invariant-section hint in the story template -----------------------


def test_template_hint_present_in_test_criteria_area() -> None:
    """Template: exactly ONE commented hint heading in the Test criteria area."""
    content = _read(TEMPLATE)

    assert content.count(INVARIANT_HEADING) == 1, (
        f"docs/features/_story_template.md: expected exactly one occurrence of "
        f"{INVARIANT_HEADING!r} (ONE commented section hint)"
    )

    hint_at = content.index(INVARIANT_HEADING)
    test_criteria_at = content.index("## Test criteria")
    tooling_at = content.index("## Tooling Gates")

    assert test_criteria_at < hint_at < tooling_at, (
        "docs/features/_story_template.md: the section hint must sit inside the "
        "Test criteria area (between '## Test criteria' and '## Tooling Gates')"
    )


def test_template_hint_is_commented() -> None:
    """The hint is an HTML comment — normal story rendering stays unchanged."""
    content = _read(TEMPLATE)
    hint_at = content.index(INVARIANT_HEADING)

    open_at = content.rindex("<!--", 0, hint_at)
    assert open_at != -1, "hint must sit inside an HTML comment (missing '<!--')"
    last_close_before = content.rindex("-->", 0, hint_at)
    assert last_close_before < open_at, (
        "hint must sit inside an HTML comment (a previous comment was already "
        "closed before the hint)"
    )
    close_at = content.index("-->", hint_at)
    assert close_at != -1, "hint must sit inside an HTML comment (missing '-->')"


def test_template_hint_has_no_clarification_marker() -> None:
    """The hint comment must not carry a literal marker into generated stories.

    plan_check scans every non-fenced story line for ``[NEEDS CLARIFICATION``;
    the hint persists verbatim into generated stories, so a marker inside the
    comment would fail plan_check for every generated story.
    """
    content = _read(TEMPLATE)
    open_at = content.rindex("<!--", 0, content.index(INVARIANT_HEADING))
    close_at = content.index("-->", open_at)
    comment = content[open_at:close_at]

    assert "[NEEDS CLARIFICATION" not in comment, (
        "_story_template.md: the invariants hint comment contains a literal "
        "'[NEEDS CLARIFICATION' marker — it persists into generated stories "
        "and would trip plan_check's clarification-marker scan"
    )


# --- (e) template constancy vs main -----------------------------------------


def test_template_constant_sections_byte_unchanged_vs_main() -> None:
    """Every template line from the branch base survives byte-identical, in order.

    Additions-only edit: the hint comment must not modify or remove any
    pre-existing line (constant sections and the debug-type comment block
    stay byte-unchanged vs main / branch base).
    """
    old_bytes = _template_blob_at_branch_base()
    if old_bytes is None:
        pytest.skip("git or 'main' unavailable — cannot diff template against main")

    old_lines = old_bytes.decode("utf-8").splitlines()
    new_lines = _read(TEMPLATE).splitlines()

    remaining = iter(new_lines)
    for line in old_lines:
        for candidate in remaining:
            if candidate == line:
                break
        else:
            pytest.fail(
                f"_story_template.md: pre-existing line removed or modified vs "
                f"main (edit must be additions-only): {line!r}"
            )
