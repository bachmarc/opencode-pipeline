"""Tests for create_story.py --type debug (Story 30-02).

Runs the REAL create_story.py — copied into a temp project so the script's
__file__-derived repo root points at the fixture — via subprocess. Covers:

- the --type debug investigation skeleton (Investigation questions,
  findings report, explicit no-fix rule; machine fields identical to
  normal stories),
- the .pipeline/escalations.json ledger append (exactly one
  {"story", "debug_story", "at"} entry per debug story), and the driver
  core yielding escalated-blocked for a story with an existing ledger
  entry and a fresh fail series,
- normal-type stories remaining byte-identical although the story
  template now carries the appended DEBUG-STORY-BODY-TEMPLATE comment
  block (create_story.py strips it for normal stories).

No external systems — the fixture is a plain temp directory tree.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CREATE_STORY = REPO_ROOT / "scripts" / "create_story.py"
TEMPLATE = REPO_ROOT / "docs" / "features" / "_story_template.md"
DEBUG_MARKER = "<!-- DEBUG-STORY-BODY-TEMPLATE"

# driver.py pure core is reused to assert the ledger -> escalated-blocked wiring.
_spec = importlib.util.spec_from_file_location("driver_debug", REPO_ROOT / "scripts" / "driver.py")
assert _spec is not None and _spec.loader is not None
driver = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(driver)

FEATURE_MD = """---
id: F-001
title: Test Feature
status: planned
owner: ""
---

## Vision

Test feature.

## Stories

"""


def _template_text(with_debug_block: bool) -> str:
    """Real story template; with_debug_block=False reconstructs the
    pre-30-02 template bytes (the appended block removed again)."""
    text = TEMPLATE.read_text(encoding="utf-8")
    idx = text.find(DEBUG_MARKER)
    if with_debug_block:
        assert idx != -1, "real template must carry the debug block after 30-02"
        return text
    assert idx != -1, "real template must carry the debug block after 30-02"
    return text[:idx].rstrip("\n") + "\n"


def _make_project(repo: Path, template_text: str) -> Path:
    """Minimal project skeleton: scripts/create_story.py + docs/features tree
    with a feature that already has story 01-01 (so new ids start at 01-02)."""
    (repo / "scripts").mkdir(parents=True)
    features = repo / "docs" / "features"
    features.mkdir(parents=True)
    shutil.copy(CREATE_STORY, repo / "scripts" / "create_story.py")
    (features / "_story_template.md").write_text(template_text, encoding="utf-8")
    feature = features / "test-feature"
    feature.mkdir()
    (feature / "feature.md").write_text(FEATURE_MD, encoding="utf-8")
    stories = feature / "stories"
    stories.mkdir()
    (stories / "01-01-earlier-story.md").write_text(
        "# Story 01-01 — Earlier Story\n\nStatus: Planned\n", encoding="utf-8"
    )
    return repo


def _run_create(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the fixture's create_story.py copy (its __file__ root is the fixture)."""
    return subprocess.run(
        [sys.executable, str(repo / "scripts" / "create_story.py"), *args],
        capture_output=True,
        text=True,
    )


def _story_path(repo: Path, story_id: str, slug: str) -> Path:
    return repo / "docs" / "features" / "test-feature" / "stories" / f"{story_id}-{slug}.md"


# ---------------------------------------------------------------------------
# test_debug_story_type — the investigation skeleton
# ---------------------------------------------------------------------------


def test_debug_story_type(tmp_path: Path) -> None:
    """--type debug writes the investigation skeleton with the required
    sections and the no-fix rule; machine fields match normal stories."""
    repo = _make_project(tmp_path / "proj", _template_text(with_debug_block=True))

    result = _run_create(
        repo, "test-feature", "investigate-failure",
        "--type", "debug", "--target-story", "01-01", "--feature", "F-001",
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["id"] == "01-02"
    assert data["story_file"].endswith("01-02-investigate-failure.md")

    content = _story_path(repo, "01-02", "investigate-failure").read_text(encoding="utf-8")

    # Investigation sections (requirement 4 / acceptance criteria).
    assert "## Investigation questions" in content
    assert "findings report" in content
    # Explicit not-fix rule.
    assert "Do NOT fix code" in content
    assert "do NOT change behavior" in content
    # Machine fields identical to normal stories.
    assert "Status: Planned" in content
    assert "Feature: test-feature (F-001)" in content
    assert "# Story 01-02 — Investigate Failure" in content

    # The feature.md index gained the debug story entry too.
    feature_md = (repo / "docs" / "features" / "test-feature" / "feature.md").read_text(
        encoding="utf-8"
    )
    assert "01-02-investigate-failure (planned)" in feature_md


# ---------------------------------------------------------------------------
# test_debug_story_appends_ledger — .pipeline/escalations.json
# ---------------------------------------------------------------------------


def test_debug_story_appends_ledger(tmp_path: Path) -> None:
    """Creating a debug story for target 01-01 appends exactly one
    {"story", "debug_story", "at"} entry to .pipeline/escalations.json; the
    driver core then yields escalated-blocked for 01-01 once its fail series
    crosses the threshold again (not a second escalate-remedy)."""
    repo = _make_project(tmp_path / "proj", _template_text(with_debug_block=True))

    result = _run_create(
        repo, "test-feature", "investigate-failure", "--type", "debug", "--target-story", "01-01"
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    new_id = json.loads(result.stdout)["id"]

    ledger_file = repo / ".pipeline" / "escalations.json"
    assert ledger_file.is_file(), "ledger file must be created on first entry"
    entries = json.loads(ledger_file.read_text(encoding="utf-8"))
    assert isinstance(entries, list) and len(entries) == 1, "exactly one entry appended"
    entry = entries[0]
    assert set(entry) == {"story", "debug_story", "at"}
    assert entry["story"] == "01-01"
    assert entry["debug_story"] == new_id
    datetime.fromisoformat(entry["at"])  # "at" is ISO 8601

    # A second debug story for the same target appends a second entry.
    result2 = _run_create(
        repo, "test-feature", "investigate-again", "--type", "debug", "--target-story", "01-01"
    )
    assert result2.returncode == 0, f"stderr: {result2.stderr}"
    entries2 = json.loads(ledger_file.read_text(encoding="utf-8"))
    assert len(entries2) == 2
    assert entries2[1]["debug_story"] == json.loads(result2.stdout)["id"]

    # Driver core on the recorded ledger: target story with a fresh fail
    # series crossing the default threshold -> escalated-blocked.
    profile = {"workflow": "default", "test_strategy": "unit-fake"}
    state = {
        "now": "2026-10-30T12:00:00+00:00",
        "intents": [],
        "stories": [{"id": "01-01", "status": "Planned"}],
        "qa_state": {
            "01-01": [{"verdict": "FAIL"}, {"verdict": "FAIL"}, {"verdict": "FAIL"}]
        },
        "escalations": entries,  # the single entry recorded above
        "worktrees": [],
    }
    actions = driver.compute_next_actions(profile, state)
    kinds = [a["kind"] for a in actions]
    assert "escalated-blocked" in kinds, actions
    assert "escalate-remedy" not in kinds, actions


# ---------------------------------------------------------------------------
# Normal-type stories stay byte-identical (template diff only added comment)
# ---------------------------------------------------------------------------


def test_normal_story_byte_identical_despite_template_block(tmp_path: Path) -> None:
    """A normal story created from the template WITH the appended debug comment
    block is byte-identical to one created from the pre-30-02 template."""
    repo_before = _make_project(tmp_path / "before", _template_text(with_debug_block=False))
    repo_after = _make_project(tmp_path / "after", _template_text(with_debug_block=True))

    args = ("test-feature", "new-story", "--feature", "F-001")
    result_before = _run_create(repo_before, *args)
    result_after = _run_create(repo_after, *args)
    assert result_before.returncode == 0, f"stderr: {result_before.stderr}"
    assert result_after.returncode == 0, f"stderr: {result_after.stderr}"

    content_before = _story_path(repo_before, "01-02", "new-story").read_text(encoding="utf-8")
    content_after = _story_path(repo_after, "01-02", "new-story").read_text(encoding="utf-8")
    assert content_after == content_before, "normal stories must remain byte-identical"
    assert DEBUG_MARKER not in content_after


# ---------------------------------------------------------------------------
# Argument validation (usage errors never create artifacts)
# ---------------------------------------------------------------------------


def test_debug_requires_target_story(tmp_path: Path) -> None:
    """--type debug without --target-story is a usage error; nothing is
    created (no story file, no ledger)."""
    repo = _make_project(tmp_path / "proj", _template_text(with_debug_block=True))

    result = _run_create(repo, "test-feature", "investigate-failure", "--type", "debug")
    assert result.returncode == 2
    assert not _story_path(repo, "01-02", "investigate-failure").exists()
    assert not (repo / ".pipeline" / "escalations.json").exists()


def test_target_story_rejected_for_normal_type(tmp_path: Path) -> None:
    """--target-story with a normal-type creation is a usage error."""
    repo = _make_project(tmp_path / "proj", _template_text(with_debug_block=True))

    result = _run_create(repo, "test-feature", "normal-story", "--target-story", "01-01")
    assert result.returncode == 2
    assert not _story_path(repo, "01-02", "normal-story").exists()
