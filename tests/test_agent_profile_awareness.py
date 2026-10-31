"""Tests for agent prompt profile awareness (Story 30-04, Tier K scoping).

Checks:
1. agents/qa-manager.md mentions profile-conditional fake criteria with the
   exact strings `unit-fake` and `e2e-docker`.
2. agents/qa-manager.md mentions `provenance` and `tier-d` (two-tier verdict).
3. agents/architect.md contains the `driver.py next` reference and a
   fail-open clause.
4. templates/AGENTS.md contains the `process.json` mention; AND the constant
   sections stay intact — verified by running check_template_constancy.py
   against the template itself (template-as-project must PASS, proving the
   new paragraph sits outside Workflow/Git conventions/Languages/Prohibitions)
   and by tests/test_check_scripts.py (the real constancy coverage — audit
   fix 2026-10-30) still existing unchanged.

Stdlib only — no external systems, deterministic (repo files are the fixture).
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

QA_MANAGER = REPO_ROOT / "agents" / "qa-manager.md"
ARCHITECT = REPO_ROOT / "agents" / "architect.md"
TEMPLATE = REPO_ROOT / "templates" / "AGENTS.md"
CHECK_SCRIPTS_TEST = REPO_ROOT / "tests" / "test_check_scripts.py"
CONSTANCY_SCRIPT = REPO_ROOT / "scripts" / "check_template_constancy.py"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing {path.relative_to(REPO_ROOT)}"
    return path.read_text(encoding="utf-8")


# --- qa-manager.md: profile-conditional fake criteria -----------------------------


def test_qa_manager_mentions_profile_strategies() -> None:
    """agents/qa-manager.md names both process profiles with exact strings."""
    content = _read(QA_MANAGER)

    assert "unit-fake" in content, (
        "qa-manager.md: missing exact string 'unit-fake' — the default profile's "
        "fake rules must be kept verbatim and labeled"
    )
    assert "e2e-docker" in content, (
        "qa-manager.md: missing exact string 'e2e-docker' — profile-conditional "
        "fake criteria (fake-parity FAIL rules do NOT apply there) must be declared"
    )


def test_qa_manager_mentions_provenance_and_tier_d() -> None:
    """agents/qa-manager.md requires provenance markers and a Tier-D-first step."""
    content = _read(QA_MANAGER)

    assert "provenance" in content, (
        "qa-manager.md: missing 'provenance' — every verdict entry must record "
        "whether it was script-verified (tier-d) or LLM-judged (tier-k)"
    )
    assert "tier-d" in content, (
        "qa-manager.md: missing 'tier-d' — deterministic checks must be consumed "
        "first (Step 0) and copied into the verdict"
    )
    assert "tier-k" in content, (
        "qa-manager.md: missing 'tier-k' — provenance marker for the "
        "non-automatable remainder judged by the LLM"
    )


def test_qa_manager_profile_misdeclaration_blocks() -> None:
    """Inconsistent/misdeclared profile escalates as BLOCKED_Requirements."""
    content = _read(QA_MANAGER)
    assert "BLOCKED_Requirements" in content, (
        "qa-manager.md: inconsistent/misdeclared profile must escalate as "
        "BLOCKED_Requirements — never a silent adaptation of criteria"
    )


# --- architect.md: driver integration ----------------------------------------------


def test_architect_mentions_driver_next() -> None:
    """agents/architect.md mandates `driver.py next` as first deterministic step."""
    content = _read(ARCHITECT)

    assert "driver.py next" in content, (
        "architect.md: missing 'driver.py next' reference — first deterministic "
        "step at session start and in Phase 3"
    )
    assert "merge_if_passed" in content, (
        "architect.md: missing 'merge_if_passed' — merge authority stays "
        "exclusively with merge_if_passed.py; driver output is advisory only"
    )


def test_architect_has_fail_open_clause() -> None:
    """agents/architect.md defines the fail-open rule (one sentence)."""
    content = _read(ARCHITECT)

    assert "fail-open" in content, (
        "architect.md: missing fail-open clause — if the driver cannot run, "
        "say so and decide explicitly with a documented reason"
    )


def test_architect_has_plan_check_step() -> None:
    """agents/architect.md runs plan_check.py before every planning checkpoint."""
    content = _read(ARCHITECT)

    assert "plan_check" in content, (
        "architect.md: missing 'plan_check' — before EVERY planning checkpoint "
        "run plan_check.py and resolve its findings (conflict candidates → "
        "sequential waves in the STORIES.md phase block)"
    )
    assert "STORIES.md" in content, (
        "architect.md: missing 'STORIES.md' — conflict candidates are declared "
        "as sequential waves in the STORIES.md phase block"
    )


# --- templates/AGENTS.md: Process Profile paragraph --------------------------------


def test_template_process_profile() -> None:
    """templates/AGENTS.md mentions process.json; constancy coverage stays intact."""
    content = _read(TEMPLATE)
    assert "process.json" in content, (
        "templates/AGENTS.md: missing 'process.json' — projects declare their "
        "process profile there; the pipeline's QA gate and driver read it"
    )

    # The real constancy coverage (audit fix 2026-10-30) must still exist
    # unchanged — tests/test_check_scripts.py covers check_template_constancy.
    assert CHECK_SCRIPTS_TEST.is_file(), (
        f"missing {CHECK_SCRIPTS_TEST.relative_to(REPO_ROOT)} — the constancy "
        f"coverage from the audit fix must not be removed"
    )

    # The new paragraph sits in a constant-safe position: the template itself
    # must still pass check_template_constancy.py (template-as-project = PASS,
    # i.e. Workflow/Git conventions/Languages/Prohibitions are recognizable
    # and unmodified).
    result = subprocess.run(
        [sys.executable, str(CONSTANCY_SCRIPT), str(TEMPLATE)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"check_template_constancy.py failed on templates/AGENTS.md "
        f"(exit {result.returncode}): {result.stdout} {result.stderr}"
    )
    output = json.loads(result.stdout)
    assert output["result"] == "PASS", f"expected PASS, got {output}"
