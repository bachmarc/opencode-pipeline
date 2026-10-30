"""Pure core tests for scripts/driver.py (Story 30-01).

Tests compute_next_actions() and validate_profile() as PURE functions:
state and profile are plain dicts passed in, no filesystem, no subprocess.
The import self-check asserts the core stays IO-free (no pathlib/subprocess,
no imports beyond stdlib typing/data structures).
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DRIVER = REPO_ROOT / "scripts" / "driver.py"

# Load driver.py as a standalone module (same pattern as tests/test_story_status.py).
_spec = importlib.util.spec_from_file_location("driver", DRIVER)
assert _spec is not None and _spec.loader is not None
driver = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(driver)

NOW = "2026-10-30T12:00:00+00:00"

DEFAULT_PROFILE = {"workflow": "default", "test_strategy": "unit-fake"}


def _iso_from_now(delta: timedelta) -> str:
    """Timestamp derived from NOW by a timedelta (ISO with +00:00 offset)."""
    base = datetime.fromisoformat(NOW)
    return (base + delta).isoformat()


# ---------------------------------------------------------------------------
# test_order_and_kinds
# ---------------------------------------------------------------------------


def test_order_and_kinds() -> None:
    """Fixture state yields intent-reminder, spawn-qa, merge-candidate, spawn-dev
    in exactly that stable order."""
    profile = dict(DEFAULT_PROFILE)
    state: dict = {
        "now": NOW,
        "intents": [
            {
                "story_id": "27-02",
                "agent": "developer",
                "step": "implementing",
                "started_at": "2026-10-25T12:00:00+00:00",  # 120h old, still open
                "done": False,
            }
        ],
        "stories": [
            {"id": "30-01", "status": "In Progress"},  # no verdicts -> spawn-qa
            {"id": "27-02", "status": "In Progress"},  # PASS, not Done -> merge-candidate
            {"id": "27-03", "status": "Planned"},  # FAIL -> spawn-dev
        ],
        "qa_state": {
            "27-02": [{"verdict": "PASS", "timestamp": "2026-10-20T00:00:00+00:00"}],
            "27-03": [{"verdict": "FAIL", "timestamp": "2026-10-20T00:00:00+00:00"}],
        },
        "worktrees": [],
    }

    actions = driver.compute_next_actions(profile, state)

    assert [a["kind"] for a in actions] == [
        "intent-reminder",
        "spawn-qa",
        "merge-candidate",
        "spawn-dev",
    ]
    by_kind = {a["kind"]: a for a in actions}
    assert by_kind["intent-reminder"]["story_id"] == "27-02"
    assert by_kind["spawn-qa"]["story_id"] == "30-01"
    assert by_kind["merge-candidate"]["story_id"] == "27-02"
    assert by_kind["spawn-dev"]["story_id"] == "27-03"
    for action in actions:
        assert "reason" in action and isinstance(action["reason"], str)


# ---------------------------------------------------------------------------
# test_no_action_when_consistent
# ---------------------------------------------------------------------------


def test_no_action_when_consistent() -> None:
    """Clean state yields exactly [{"kind": "no-action"}]."""
    profile = dict(DEFAULT_PROFILE)
    state: dict = {
        "now": NOW,
        "intents": [
            # A finished intent must never trigger a reminder.
            {"story_id": "99-01", "started_at": "2020-01-01T00:00:00+00:00", "done": True},
            # A fresh open intent is fine.
            {
                "story_id": "99-02",
                "started_at": _iso_from_now(-timedelta(hours=1)),  # started 1h ago
                "done": False,
            },
        ],
        "stories": [
            {"id": "99-01", "status": "Done (QA PASS, abc1234)"},  # merged, PASS verdict
            {"id": "99-02", "status": "Planned"},  # planned, no verdicts expected
        ],
        "qa_state": {"99-01": [{"verdict": "PASS", "timestamp": "2026-10-29T00:00:00+00:00"}]},
        "worktrees": [],
    }

    actions = driver.compute_next_actions(profile, state)

    assert actions == [{"kind": "no-action"}]


# ---------------------------------------------------------------------------
# test_stale_intent_threshold
# ---------------------------------------------------------------------------


def test_stale_intent_threshold() -> None:
    """Intent older than threshold -> reminder; fresh intent -> no reminder."""
    profile = dict(DEFAULT_PROFILE, intent_max_age_hours=72)
    fresh_intent = {
        "story_id": "27-02",
        "agent": "developer",
        "step": "implementing",
        "started_at": _iso_from_now(-timedelta(hours=1)),  # started 1h ago
        "done": False,
    }
    empty_state: dict = {"now": NOW, "intents": [], "stories": [], "qa_state": {}, "worktrees": []}

    # Exactly 72h old is NOT older than the threshold -> no reminder.
    exact_intent = dict(fresh_intent, started_at=_iso_from_now(-timedelta(hours=72)))
    assert driver.compute_next_actions(profile, dict(empty_state, intents=[exact_intent])) == [
        {"kind": "no-action"}
    ]

    # One second past the threshold -> reminder for the intent's story.
    stale_intent = dict(fresh_intent, started_at=_iso_from_now(-timedelta(hours=72, seconds=1)))
    actions = driver.compute_next_actions(profile, dict(empty_state, intents=[stale_intent]))
    assert [a["kind"] for a in actions] == ["intent-reminder"]
    assert actions[0]["story_id"] == "27-02"

    # Fresh intent -> no reminder.
    actions = driver.compute_next_actions(profile, dict(empty_state, intents=[fresh_intent]))
    assert [a["kind"] for a in actions] == ["no-action"]

    # Default threshold (no intent_max_age_hours key in profile) is 72h.
    actions = driver.compute_next_actions(DEFAULT_PROFILE, dict(empty_state, intents=[stale_intent]))
    assert [a["kind"] for a in actions] == ["intent-reminder"]


# ---------------------------------------------------------------------------
# test_unknown_profile_keys_ignored
# ---------------------------------------------------------------------------


def test_unknown_profile_keys_ignored() -> None:
    """Extra profile keys do not change actions and do not raise."""
    state: dict = {
        "now": NOW,
        "intents": [
            {"story_id": "27-02", "started_at": "2020-01-01T00:00:00+00:00", "done": False}
        ],
        "stories": [{"id": "27-02", "status": "In Progress"}],
        "qa_state": {"27-02": [{"verdict": "PASS"}]},
        "worktrees": [],
    }

    base_actions = driver.compute_next_actions(DEFAULT_PROFILE, state)

    extended = dict(
        DEFAULT_PROFILE,
        escalation_threshold=3,
        notes="project-specific override",
        owner_team="platform",
    )
    assert driver.compute_next_actions(extended, state) == base_actions
    # Sanity: the base state itself produced non-no-action findings.
    assert base_actions != [{"kind": "no-action"}]


# ---------------------------------------------------------------------------
# validate_profile (pure profile validation)
# ---------------------------------------------------------------------------


def test_validate_profile_pass() -> None:
    report = driver.validate_profile(dict(DEFAULT_PROFILE))
    assert report["errors"] == []
    assert report["warnings"] == []


def test_validate_profile_missing_workflow() -> None:
    """Missing `workflow` key -> error naming the missing key."""
    report = driver.validate_profile({"test_strategy": "unit-fake"})
    assert report["errors"], "expected an error for missing workflow key"
    assert any("workflow" in err for err in report["errors"])


def test_validate_profile_unknown_keys_warn_only() -> None:
    """Unknown extra keys -> warnings, still valid."""
    report = driver.validate_profile(
        dict(DEFAULT_PROFILE, escalation_threshold=3, notes="custom")
    )
    assert report["errors"] == []
    assert len(report["warnings"]) == 2
    assert any("escalation_threshold" in w for w in report["warnings"])
    assert any("notes" in w for w in report["warnings"])


def test_validate_profile_invalid_values() -> None:
    """Known keys with invalid values fail loudly."""
    report = driver.validate_profile(dict(DEFAULT_PROFILE, workflow="improvise"))
    assert any("workflow" in err for err in report["errors"])
    report = driver.validate_profile(dict(DEFAULT_PROFILE, test_strategy="yolo"))
    assert any("test_strategy" in err for err in report["errors"])
    report = driver.validate_profile(dict(DEFAULT_PROFILE, intent_max_age_hours="soon"))
    assert any("intent_max_age_hours" in err for err in report["errors"])


def test_default_profile_builtin() -> None:
    """Built-in default profile: workflow=default, test_strategy=unit-fake, 72h."""
    assert driver.DEFAULT_PROFILE == {
        "workflow": "default",
        "test_strategy": "unit-fake",
        "intent_max_age_hours": 72,
    }


# ---------------------------------------------------------------------------
# Acceptance: pure core has no pathlib/subprocess/imports beyond stdlib
# ---------------------------------------------------------------------------


def test_module_imports_imports_pure() -> None:
    """Self-check via AST: module imports only stdlib; NO pathlib/subprocess;
    the pure core functions contain no imports or I/O module references."""
    assert DRIVER.exists(), f"Script not found: {DRIVER}"
    tree = ast.parse(DRIVER.read_text(encoding="utf-8"))

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert "pathlib" not in imported
    assert "subprocess" not in imported
    nonstdlib = imported - set(sys.stdlib_module_names) - {"__future__"}
    assert not nonstdlib, f"non-stdlib module imports: {sorted(nonstdlib)}"

    for func_name in ("compute_next_actions", "validate_profile"):
        func = next(
            n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func_name
        )
        # No imports inside the pure core.
        assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(func))
        # No I/O module references in the pure core (source-level check).
        used_names = {n.id for n in ast.walk(func) if isinstance(n, ast.Name)}
        used_attrs = {n.attr for n in ast.walk(func) if isinstance(n, ast.Attribute)}
        for forbidden in ("pathlib", "subprocess", "os", "open", "Path"):
            assert forbidden not in used_names, f"{func_name} references {forbidden}"
            assert forbidden not in used_attrs, f"{func_name} references attribute {forbidden}"
