#!/usr/bin/env python3
"""Process driver: compute the next required pipeline actions from data.

Deterministic replacement for "an LLM as state machine": given the pipeline
state (story statuses, QA verdicts, open intents) and a per-project process
profile, the driver computes the next required actions as machine-readable
JSON — no LLM required to decide. The architect acts ONLY on the driver's
output.

Design (Stories 30-01 + 30-02, F-030):

- PURE core: ``compute_next_actions(profile, state)`` takes plain dicts in and
  returns plain data out. The core imports NOTHING besides stdlib typing /
  data structures — no pathlib, no subprocess, no I/O. The CLI adapter wires
  real files.
- Profile (`.pipeline/process.json`) is data, not code. Known keys:
  - ``workflow``: ``"default" | "custom"`` (required)
  - ``test_strategy``: ``"unit-fake" | "e2e-docker" | "hybrid"`` (default
    ``unit-fake``)
  - ``intent_max_age_hours``: int, threshold for intent-reminder (default 72)
  - ``escalation``: dict with ``fail_loop`` (default 3) and
    ``max_escalations`` (default 2); see escalation semantics below
  Unknown extra keys are ignored silently by the core (extensibility rule)
  and reported as warnings by validation — never fatal.
- Action kinds, in STABLE order:
  - ``intent-reminder``: an open intent older than ``intent_max_age_hours``.
  - ``spawn-qa``: story is dev-done/committed (status not Planned/Done) but no
    QA verdict exists.
  - ``merge-candidate``: latest QA verdict is PASS but the story is not Done.
  - ``spawn-dev``: story status Planned/In-Progress with a FAIL verdict whose
    current fail series is BELOW the escalation threshold (at/above the
    threshold the escalation kinds replace the pointless retry).
  - ``escalate-remedy``: the current fail series crossed the escalation
    threshold and the story has escalation budget left.
  - ``escalated-blocked``: threshold crossed again with the escalation budget
    exhausted — the story is handed back to the user.
  - ``no-action``: state fully consistent (never omitted; reported explicitly).
- Escalation semantics (30-02): the FAIL series of a story is its trailing
  run of consecutive FAIL verdicts — a PASS (any non-FAIL verdict) RESETS the
  series. Escalations already happened are read from the escalation ledger
  ``.pipeline/escalations.json`` (a JSON array of
  ``{"story": <id>, "debug_story": <id>, "at": <iso8601>}`` entries, appended
  by ``create_story.py --type debug`` — the stateless driver only COUNTS
  entries per story from this ledger; it never writes it). Every threshold
  crossing of the fail series consumes one escalation event: recorded
  entries plus the current crossing stay below ``max_escalations`` →
  ``escalate-remedy`` with the RECOMMENDATION pair ``recommendation:
  "debug-story"`` + ``diagnosis: "strong-architect"`` (the driver emits both
  as payload fields and names both in the reason text, but implements
  nothing itself); reaching ``max_escalations`` → ``escalated-blocked`` →
  "block-and-ask-user" (stop automated retries, ask the user). Escalate
  actions sort LAST in the stable order. ``fail_loop <= 0`` disables the
  feature entirely (no escalate actions ever); a missing/malformed
  ``escalation`` profile block uses the default values.
- Driver is READ-ONLY/advisory: it never mutates state, there is no
  ``--apply``. Merge authority stays exclusively with ``merge_if_passed.py``;
  the escalation ledger is written exclusively by ``create_story.py``.

Story statuses are parsed from the ``Status:`` lines of
``docs/features/*/stories/*.md`` (same pattern as ``scripts/story_status.py``)
— NOT from the STORIES.md markdown table.

Usage:
    driver.py next [--profile PATH]      compute next actions, print JSON
    driver.py validate [--profile PATH]  validate profile only, exit 0/1

Exit codes: 0 ok, 1 validation failure, 2 usage error (argparse).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

# Built-in default profile when the profile file is missing.
DEFAULT_PROFILE: dict = {
    "workflow": "default",
    "test_strategy": "unit-fake",
    "intent_max_age_hours": 72,
}

# Escalation defaults (Story 30-02) — used when the profile has no (or a
# malformed) "escalation" block. fail_loop <= 0 disables the feature.
DEFAULT_FAIL_LOOP = 3
DEFAULT_MAX_ESCALATIONS = 2

# Profile keys consumed by this story; anything else is an unknown extra key.
KNOWN_PROFILE_KEYS = frozenset(
    {"workflow", "test_strategy", "intent_max_age_hours", "escalation"}
)
KNOWN_WORKFLOWS = ("default", "custom")
KNOWN_TEST_STRATEGIES = ("unit-fake", "e2e-docker", "hybrid")

# Action kinds in the stable output order (requirement 3; Story 30-02 appends
# the escalation kinds LAST — after spawn-dev).
_ACTION_ORDER = (
    "intent-reminder",
    "spawn-qa",
    "merge-candidate",
    "spawn-dev",
    "escalate-remedy",
    "escalated-blocked",
)


# ---------------------------------------------------------------------------
# Pure core — no I/O, only stdlib data structures.
# ---------------------------------------------------------------------------


def compute_next_actions(profile: dict, state: dict) -> list[dict]:
    """Compute next actions from profile + state. PURE function.

    profile keys consumed: ``intent_max_age_hours`` (default 72) and the
    ``escalation`` block (``fail_loop`` default 3, ``max_escalations``
    default 2). All other profile keys are ignored silently.

    state is a plain dict:
        stories:     [{id, status}]
        qa_state:    {story_id: [verdict...]}  (verdict: {"verdict": "PASS"} |
                     "PASS" — the LAST entry is the latest)
        intents:     [{story_id, started_at, done, ...}]
        escalations: [{"story": <id>, "debug_story": <id>, "at": <iso>}] —
                     the escalation ledger (30-02); entries for other stories
                     are ignored. Optional; missing means zero escalations.
        worktrees:   [names...]  (reserved for future fail-loop worktree
                     checks, ignored here)
        now:         optional ISO timestamp used as "current time" (tests);
                     defaults to the real current UTC time.

    Returns actions as {kind, story_id?, reason, ...} in the stable order
    intent-reminder, spawn-qa, merge-candidate, spawn-dev, escalate-remedy,
    escalated-blocked — or exactly one {"kind": "no-action"} when the state
    is fully consistent.
    """
    threshold = profile.get("intent_max_age_hours", DEFAULT_PROFILE["intent_max_age_hours"])
    fail_loop, max_escalations = _escalation_settings(profile)
    escalations = state.get("escalations") or []
    now = _parse_iso(state.get("now")) or datetime.now(timezone.utc)

    actions: list[dict] = []

    # intent-reminder: open intent older than the threshold.
    for intent in state.get("intents") or []:
        if intent.get("done"):
            continue
        started_at = _parse_iso(intent.get("started_at"))
        if started_at is None:
            continue
        age_hours = (now - started_at).total_seconds() / 3600.0
        if age_hours > threshold:
            actions.append(
                {
                    "kind": "intent-reminder",
                    "story_id": intent.get("story_id"),
                    "reason": (
                        f"Intent open for {age_hours:.1f}h (threshold {threshold}h) — "
                        "resolve it via intent.py done or continue the work it tracks"
                    ),
                }
            )

    qa_state = state.get("qa_state") or {}
    for story in state.get("stories") or []:
        story_id = story.get("id")
        status = str(story.get("status") or "")
        verdicts = qa_state.get(story_id) or []
        latest_verdict = _latest_verdict(verdicts)

        # spawn-qa: dev-done/committed (not Planned, not Done) but no verdict yet.
        if _is_qa_candidate(status) and not verdicts:
            actions.append(
                {
                    "kind": "spawn-qa",
                    "story_id": story_id,
                    "reason": f"Story status '{status}' with no QA verdict — spawn QA",
                }
            )

        # merge-candidate: latest verdict PASS, story not Done.
        if latest_verdict == "PASS" and not _is_done(status):
            actions.append(
                {
                    "kind": "merge-candidate",
                    "story_id": story_id,
                    "reason": "Latest QA verdict is PASS and story is not Done — "
                    "merge via merge_if_passed.py",
                }
            )

        # Escalation (30-02): the current fail series crossed the threshold.
        # The escalation action REPLACES the routine spawn-dev retry for this
        # story — the fail loop must break, not repeat (see module docstring).
        fail_series = _consecutive_fails(verdicts)
        if fail_loop > 0 and fail_series >= fail_loop:
            escalation_events = _escalation_count(escalations, story_id) + 1
            if escalation_events >= max_escalations:
                actions.append(
                    {
                        "kind": "escalated-blocked",
                        "story_id": story_id,
                        "reason": (
                            f"Fail loop persists: {fail_series} consecutive FAILs "
                            f"(threshold {fail_loop}) with {escalation_events - 1} escalation(s) "
                            f"already recorded (max_escalations {max_escalations}) — "
                            "block-and-ask-user: stop automated retries and ask the user"
                        ),
                    }
                )
            else:
                actions.append(
                    {
                        "kind": "escalate-remedy",
                        "story_id": story_id,
                        "recommendation": "debug-story",
                        "diagnosis": "strong-architect",
                        "reason": (
                            f"Fail loop: {fail_series} consecutive FAILs (threshold {fail_loop}) — "
                            "RECOMMENDATION pair: recommendation=debug-story (create an "
                            "investigation story via create_story.py --type debug) and "
                            "diagnosis=strong-architect (strong-tier root-cause review); "
                            "the driver implements nothing itself"
                        ),
                    }
                )

        # spawn-dev: Planned/In-Progress with a FAIL verdict BELOW the escalation
        # threshold (at/above it the escalation kinds above replace the retry).
        elif latest_verdict == "FAIL" and status in ("Planned", "In Progress"):
            actions.append(
                {
                    "kind": "spawn-dev",
                    "story_id": story_id,
                    "reason": "Latest QA verdict is FAIL — spawn developer to fix",
                }
            )

    actions.sort(key=_stable_sort_key)

    if not actions:
        actions.append({"kind": "no-action"})
    return actions


def validate_profile(profile: dict) -> dict:
    """Validate a process profile. PURE function.

    Returns {"errors": [str], "warnings": [str]}:
    - missing required key ``workflow`` -> error naming the missing key;
    - known keys with invalid values -> errors (fails loudly);
    - unknown extra keys -> warnings only (additive fields tolerated).
    """
    errors: list[str] = []
    warnings: list[str] = []

    if "workflow" not in profile:
        errors.append("Missing required profile key: workflow")
    elif profile["workflow"] not in KNOWN_WORKFLOWS:
        errors.append(
            f"Invalid workflow value {profile['workflow']!r} "
            f"(expected one of {', '.join(KNOWN_WORKFLOWS)})"
        )

    if "test_strategy" in profile and profile["test_strategy"] not in KNOWN_TEST_STRATEGIES:
        errors.append(
            f"Invalid test_strategy value {profile['test_strategy']!r} "
            f"(expected one of {', '.join(KNOWN_TEST_STRATEGIES)})"
        )

    if "intent_max_age_hours" in profile:
        value = profile["intent_max_age_hours"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            errors.append(
                f"Invalid intent_max_age_hours value {value!r} (expected a non-negative number)"
            )

    for key in sorted(profile):
        if key not in KNOWN_PROFILE_KEYS:
            warnings.append(f"Unknown profile key ignored: {key}")

    return {"errors": errors, "warnings": warnings}


def _parse_iso(value: Any) -> datetime | None:
    """Parse an ISO timestamp; None when missing/unparseable."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _latest_verdict(verdicts: list) -> str | None:
    """Latest verdict from a verdict list ({"verdict": X} entries or plain strings)."""
    if not verdicts:
        return None
    latest = verdicts[-1]
    if isinstance(latest, dict):
        return latest.get("verdict")
    if isinstance(latest, str):
        return latest
    return None


def _consecutive_fails(verdicts: list) -> int:
    """Trailing consecutive FAIL verdicts of the CURRENT attempt series.

    The first non-FAIL verdict (PASS or anything else) reading backwards
    resets the counter — a PASS ends the current fail series. Accepts both
    {"verdict": X} entries and plain strings.
    """
    series = 0
    for entry in reversed(verdicts):
        verdict = entry.get("verdict") if isinstance(entry, dict) else entry
        if verdict == "FAIL":
            series += 1
        else:
            break
    return series


def _escalation_settings(profile: dict) -> tuple[int, int]:
    """(fail_loop, max_escalations) from the profile's ``escalation`` block.

    A missing or malformed block yields the defaults (3, 2); non-numeric
    values fall back to the defaults as well. ``fail_loop <= 0`` disables
    the escalation feature (checked by the caller).
    """
    block = profile.get("escalation")
    if not isinstance(block, dict):
        return DEFAULT_FAIL_LOOP, DEFAULT_MAX_ESCALATIONS

    def _number(value: object, default: int) -> int:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return default
        return int(value)

    fail_loop = _number(block.get("fail_loop", DEFAULT_FAIL_LOOP), DEFAULT_FAIL_LOOP)
    max_escalations = _number(
        block.get("max_escalations", DEFAULT_MAX_ESCALATIONS), DEFAULT_MAX_ESCALATIONS
    )
    return fail_loop, max_escalations


def _escalation_count(escalations: list, story_id: object) -> int:
    """Number of escalation-ledger entries recorded for story_id.

    The ledger is a list of {"story": <id>, "debug_story": <id>, "at": <iso>}
    entries (appended by create_story.py --type debug); missing or malformed
    entries are ignored.
    """
    return sum(
        1
        for entry in escalations
        if isinstance(entry, dict) and entry.get("story") == story_id
    )


def _is_done(status: str) -> bool:
    """True for "Done*" statuses ("Done", "Done (QA PASS, abc)", "Done (abc)")."""
    return status.startswith("Done")


def _is_qa_candidate(status: str) -> bool:
    """Dev-done/committed-ish: work happened but QA has not merged (not Done*)."""
    return status != "" and status != "Planned" and not _is_done(status)


def _stable_sort_key(action: dict) -> tuple[int, str]:
    """Order by _ACTION_ORDER, then by story_id for determinism."""
    kind = action.get("kind", "")
    try:
        index = _ACTION_ORDER.index(kind)
    except ValueError:
        index = len(_ACTION_ORDER)
    return (index, str(action.get("story_id") or ""))


# ---------------------------------------------------------------------------
# CLI adapter — thin, read-only I/O layer around the pure core.
# ---------------------------------------------------------------------------


def get_repo_root() -> str:
    """Repo root via CWD git-traversal (same pattern as story_status.py):
    walks up until a `.git` entry exists; falls back to the starting CWD."""
    current = os.getcwd()
    start = current
    while True:
        if os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return start
        current = parent


def load_profile(path: str) -> tuple[dict, bool]:
    """Load the profile from `path`. A missing (or unreadable) profile file
    yields the built-in DEFAULT_PROFILE. Returns (profile, file_existed)."""
    if not os.path.isfile(path):
        return dict(DEFAULT_PROFILE), False
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return dict(DEFAULT_PROFILE), False
    return (data if isinstance(data, dict) else dict(DEFAULT_PROFILE)), True


def read_stories(repo_root: str) -> list[dict]:
    """Story statuses from the `Status:` lines of docs/features/*/stories/*.md
    (NOT from the STORIES.md table). Files without a Status: line are skipped."""
    stories: list[dict] = []
    features_dir = os.path.join(repo_root, "docs", "features")
    if not os.path.isdir(features_dir):
        return stories
    for feature_name in sorted(os.listdir(features_dir)):
        stories_dir = os.path.join(features_dir, feature_name, "stories")
        if feature_name.startswith("_") or not os.path.isdir(stories_dir):
            continue
        for story_name in sorted(os.listdir(stories_dir)):
            if not story_name.endswith(".md"):
                continue
            parts = story_name[:-3].split("-", 2)
            if len(parts) < 2:
                continue
            status = _read_status_line(os.path.join(stories_dir, story_name))
            if status is None:
                continue
            stories.append({"id": f"{parts[0]}-{parts[1]}", "status": status})
    return stories


def _read_status_line(path: str) -> str | None:
    """First `Status:` line of a file, stripped value; None when absent."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("Status:"):
                    return line.split(":", 1)[1].strip()
    except (OSError, UnicodeDecodeError):
        pass
    return None


def read_qa_state(repo_root: str) -> dict:
    """QA verdicts from .pipeline/qa-state/*.json keyed by story id."""
    qa_state: dict = {}
    qa_dir = os.path.join(repo_root, ".pipeline", "qa-state")
    if not os.path.isdir(qa_dir):
        return qa_state
    for name in sorted(os.listdir(qa_dir)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(qa_dir, name), "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            continue
        verdicts = data.get("verdicts", []) if isinstance(data, dict) else data
        if isinstance(verdicts, list):
            qa_state[name[: -len(".json")]] = verdicts
    return qa_state


def read_intents(repo_root: str) -> list[dict]:
    """Open intents from .pipeline/intent.json ({intents: [...]})"""
    path = os.path.join(repo_root, ".pipeline", "intent.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    intents = data.get("intents", []) if isinstance(data, dict) else []
    return [intent for intent in intents if isinstance(intent, dict)]


def read_worktrees(repo_root: str) -> list[str]:
    """Worktree names for the state dict. Reserved for future fail-loop
    worktree-discipline checks; the core ignores worktrees, and listing them
    would require subprocess — which driver.py forbids (pure core, no
    pathlib/subprocess). The driver therefore reports no worktrees."""
    return []


def read_escalations(repo_root: str) -> list[dict]:
    """Escalation ledger entries from .pipeline/escalations.json (Story 30-02).

    The ledger is a JSON array of {"story", "debug_story", "at"} entries,
    appended by create_story.py --type debug. A missing or corrupt file, or a
    non-array payload, yields [] (a {"escalations": [...]} wrapper is
    tolerated). The driver never writes this file."""
    path = os.path.join(repo_root, ".pipeline", "escalations.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return []
    if isinstance(data, list):
        return [entry for entry in data if isinstance(entry, dict)]
    if isinstance(data, dict) and isinstance(data.get("escalations"), list):
        return [entry for entry in data["escalations"] if isinstance(entry, dict)]
    return []


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        prog="driver.py",
        description="Process driver: compute next pipeline actions (read-only, advisory).",
    )
    parser.add_argument(
        "command",
        choices=["next", "validate"],
        help="next: compute actions; validate: validate profile only",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Path to the process profile (default: <repo-root>/.pipeline/process.json)",
    )
    args = parser.parse_args(argv)

    repo_root = get_repo_root()
    profile_path = args.profile or os.path.join(repo_root, ".pipeline", "process.json")
    profile, _existed = load_profile(profile_path)

    if args.command == "validate":
        report = validate_profile(profile)
        payload: dict = {}
        if report["warnings"]:
            payload["warnings"] = report["warnings"]
        if report["errors"]:
            payload["result"] = "FAIL"
            payload["errors"] = report["errors"]
            print(json.dumps(payload))
            return 1
        payload["result"] = "PASS"
        print(json.dumps(payload))
        return 0

    # next
    state = {
        "stories": read_stories(repo_root),
        "qa_state": read_qa_state(repo_root),
        "intents": read_intents(repo_root),
        "escalations": read_escalations(repo_root),
        "worktrees": read_worktrees(repo_root),
        "now": datetime.now(timezone.utc).isoformat(),
    }
    for warning in validate_profile(profile)["warnings"]:
        print(warning, file=sys.stderr)
    print(json.dumps(compute_next_actions(profile, state), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
