"""Escalation core tests for scripts/driver.py (Story 30-02).

Pure-core coverage of the escalation rules: consecutive-fail counting (a
PASS resets the series), the escalate-remedy / escalated-blocked action
kinds, threshold edge cases (``fail_loop: 0`` disables the feature; a
missing ``escalation`` block uses the defaults; ``max_escalations`` caps
the escalation budget), the stable action order (escalate actions sort
LAST), and the ``.pipeline/escalations.json`` ledger adapter.

Core tests pass plain dicts — no filesystem, no subprocess (same pattern
as tests/test_driver_core.py). The ledger ADAPTER test uses tmp_path.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DRIVER = REPO_ROOT / "scripts" / "driver.py"

# Load driver.py as a standalone module (same pattern as tests/test_driver_core.py).
_spec = importlib.util.spec_from_file_location("driver_escalation", DRIVER)
assert _spec is not None and _spec.loader is not None
driver = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(driver)

NOW = "2026-10-30T12:00:00+00:00"

DEFAULT_PROFILE = {"workflow": "default", "test_strategy": "unit-fake"}


def _verdict(name: str) -> dict:
    """Verdict entry as stored in .pipeline/qa-state/<story>.json."""
    return {"verdict": name, "timestamp": NOW}


def _state(
    verdicts: list,
    story_id: str = "30-01",
    status: str = "Planned",
    escalations: list | None = None,
) -> dict:
    """Minimal state dict: one story with the given verdict series."""
    return {
        "now": NOW,
        "intents": [],
        "stories": [{"id": story_id, "status": status}],
        "qa_state": {story_id: list(verdicts)},
        "escalations": list(escalations or []),
        "worktrees": [],
    }


def _ledger_entry(story_id: str = "30-01", debug_story: str = "30-07") -> dict:
    """Ledger entry as appended by create_story.py --type debug."""
    return {"story": story_id, "debug_story": debug_story, "at": NOW}


# ---------------------------------------------------------------------------
# test_three_fails_triggers_remedy
# ---------------------------------------------------------------------------


def test_three_fails_triggers_remedy() -> None:
    """3 consecutive FAILs (>= default fail_loop 3, no escalation recorded yet)
    yield escalate-remedy with BOTH recommendation types named — as payload
    fields AND as a pair in the reason text. The remedy replaces the routine
    spawn-dev retry (the fail loop must break, not repeat)."""
    actions = driver.compute_next_actions(DEFAULT_PROFILE, _state([_verdict("FAIL")] * 3))

    assert [a["kind"] for a in actions] == ["escalate-remedy"]
    action = actions[0]
    assert action["story_id"] == "30-01"
    assert action["recommendation"] == "debug-story"
    assert action["diagnosis"] == "strong-architect"
    assert "debug-story" in action["reason"], action["reason"]
    assert "strong-architect" in action["reason"], action["reason"]

    # Threshold boundary: 2 consecutive FAILs are BELOW the default fail_loop 3
    # -> the plain spawn-dev rule applies, no escalation action.
    below = driver.compute_next_actions(DEFAULT_PROFILE, _state([_verdict("FAIL")] * 2))
    assert [a["kind"] for a in below] == ["spawn-dev"]


# ---------------------------------------------------------------------------
# test_pass_resets_counter
# ---------------------------------------------------------------------------


def test_pass_resets_counter() -> None:
    """FAIL, FAIL, PASS, FAIL -> the current attempt series is 1 FAIL (the PASS
    reset the counter): below the threshold, so spawn-dev instead of an
    escalation action."""
    verdicts = [_verdict("FAIL"), _verdict("FAIL"), _verdict("PASS"), _verdict("FAIL")]

    assert driver._consecutive_fails(verdicts) == 1

    actions = driver.compute_next_actions(DEFAULT_PROFILE, _state(verdicts))
    assert [a["kind"] for a in actions] == ["spawn-dev"]

    # A series that reached the threshold BEFORE a PASS must not escalate after
    # the reset either: FAIL, FAIL, FAIL, PASS, FAIL -> series 1.
    assert driver._consecutive_fails(
        [_verdict("FAIL"), _verdict("FAIL"), _verdict("FAIL"), _verdict("PASS"), _verdict("FAIL")]
    ) == 1


# ---------------------------------------------------------------------------
# test_disabled_threshold
# ---------------------------------------------------------------------------


def test_disabled_threshold() -> None:
    """fail_loop: 0 disables the feature — never any escalate action, the
    plain spawn-dev rule stays in effect, even with ledger entries present."""
    profile = dict(DEFAULT_PROFILE, escalation={"fail_loop": 0})
    escalations = [_ledger_entry()]

    actions = driver.compute_next_actions(
        profile, _state([_verdict("FAIL")] * 5, escalations=escalations)
    )
    assert [a["kind"] for a in actions] == ["spawn-dev"]

    # A malformed escalation block must not crash and falls back to the
    # defaults (requirement: missing/malformed block -> default values), so
    # 5 consecutive FAILs exceed the default fail_loop 3 -> escalate-remedy.
    broken = dict(DEFAULT_PROFILE, escalation="nonsense")
    actions = driver.compute_next_actions(broken, _state([_verdict("FAIL")] * 5))
    assert [a["kind"] for a in actions] == ["escalate-remedy"]


# ---------------------------------------------------------------------------
# test_max_escalations_ask_user
# ---------------------------------------------------------------------------


def test_max_escalations_ask_user() -> None:
    """Escalation budget: each threshold crossing is one escalation event.
    recorded ledger entries + the current crossing >= max_escalations
    (default 2) -> escalated-blocked -> "block-and-ask-user" (stop automated
    retries, ask the user) instead of a second escalate-remedy."""
    # No escalation recorded: crossing #1 of 2 -> escalate-remedy.
    actions = driver.compute_next_actions(DEFAULT_PROFILE, _state([_verdict("FAIL")] * 3))
    assert [a["kind"] for a in actions] == ["escalate-remedy"]

    # One escalation recorded (debug story exists): crossing #2 of 2 ->
    # budget exhausted -> escalated-blocked, NOT a second escalate-remedy.
    ledger = [_ledger_entry()]
    actions = driver.compute_next_actions(
        DEFAULT_PROFILE, _state([_verdict("FAIL")] * 3, escalations=ledger)
    )
    assert [a["kind"] for a in actions] == ["escalated-blocked"]
    assert "block-and-ask-user" in actions[0]["reason"], actions[0]["reason"]
    assert actions[0]["story_id"] == "30-01"

    # Beyond the cap it stays blocked (no third remedy, no respawn).
    ledger2 = ledger + [_ledger_entry(debug_story="30-08")]
    actions = driver.compute_next_actions(
        DEFAULT_PROFILE, _state([_verdict("FAIL")] * 4, escalations=ledger2)
    )
    assert [a["kind"] for a in actions] == ["escalated-blocked"]


def test_ledger_counts_only_matching_story() -> None:
    """Ledger entries for OTHER stories do not consume this story's budget."""
    ledger = [_ledger_entry(story_id="30-02")]
    actions = driver.compute_next_actions(
        DEFAULT_PROFILE, _state([_verdict("FAIL")] * 3, escalations=ledger)
    )
    assert [a["kind"] for a in actions] == ["escalate-remedy"]


# ---------------------------------------------------------------------------
# Stable action order: escalate actions sort LAST (after spawn-dev)
# ---------------------------------------------------------------------------


def test_escalation_sorts_last() -> None:
    """A state exercising every kind yields the exact stable order with the
    escalation action LAST (after spawn-dev)."""
    state: dict = {
        "now": NOW,
        "intents": [
            {"story_id": "99-01", "started_at": "2020-01-01T00:00:00+00:00", "done": False}
        ],
        "stories": [
            {"id": "99-01", "status": "In Progress"},  # intent-reminder + spawn-qa
            {"id": "99-02", "status": "In Progress"},  # PASS, not Done -> merge-candidate
            {"id": "99-03", "status": "Planned"},  # single FAIL -> spawn-dev
            {"id": "30-01", "status": "Planned"},  # 3 FAILs -> escalate-remedy
        ],
        "qa_state": {
            "99-02": [_verdict("PASS")],
            "99-03": [_verdict("FAIL")],
            "30-01": [_verdict("FAIL"), _verdict("FAIL"), _verdict("FAIL")],
        },
        "escalations": [],
        "worktrees": [],
    }

    actions = driver.compute_next_actions(DEFAULT_PROFILE, state)

    assert [a["kind"] for a in actions] == [
        "intent-reminder",
        "spawn-qa",
        "merge-candidate",
        "spawn-dev",
        "escalate-remedy",
    ]
    assert actions[-1]["story_id"] == "30-01"


# ---------------------------------------------------------------------------
# Ledger adapter (CLI side): .pipeline/escalations.json
# ---------------------------------------------------------------------------


def test_read_escalations_adapter(tmp_path: Path) -> None:
    """read_escalations: missing file -> []; corrupt JSON -> []; a JSON array
    of entry dicts is passed through; {"escalations": [...]} is tolerated."""
    root = tmp_path
    assert driver.read_escalations(str(root)) == []

    pipeline = root / ".pipeline"
    pipeline.mkdir()
    ledger = pipeline / "escalations.json"

    ledger.write_text("{not json", encoding="utf-8")
    assert driver.read_escalations(str(root)) == []

    entries = [_ledger_entry(), _ledger_entry(story_id="30-02", debug_story="30-08")]
    ledger.write_text(
        '[{"story": "30-01", "debug_story": "30-07", "at": "' + NOW + '"}, '
        '{"story": "30-02", "debug_story": "30-08", "at": "' + NOW + '"}]',
        encoding="utf-8",
    )
    assert driver.read_escalations(str(root)) == entries

    ledger.write_text(
        '{"escalations": [{"story": "30-01", "debug_story": "30-07", "at": "' + NOW + '"}]}',
        encoding="utf-8",
    )
    assert driver.read_escalations(str(root)) == [_ledger_entry()]

    ledger.write_text('{"something": "else"}', encoding="utf-8")
    assert driver.read_escalations(str(root)) == []
