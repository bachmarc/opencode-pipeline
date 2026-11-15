"""Tests for scripts/plan_check.py — deterministic planning QA (Story 30-05).

Fixture story files are written into tmp_path and checked via subprocess
invocation (same pattern as tests/test_check_scripts.py). Exit codes and the
JSON contract {"result", "problems", "conflict_candidates"} are asserted.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAN_CHECK = REPO_ROOT / "scripts" / "plan_check.py"

STORY_TEMPLATE = """# Story {sid} — fixture story

Status: {status}
Feature: Fixture (F-999)

## Codebase Snapshot

- `docs/features/_story_template.md` — the story skeleton used by create_story.py.

## Context / Purpose

Fixture purpose text for the plan_check test suite.

## Requirements

{requirements}

## Developer Targets (exactly, no more / no less)

{targets}

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- Fixture criterion verified.

## Test criteria (must exist BEFORE implementation)

- `tests/test_fixture.py::test_fixture_case`


"""


def write_story(root: Path, name: str, status: str = "Planned",
                requirements: str = "1. Do the fixture thing.",
                targets: str = "- Create `scripts/fixture_new.py`.") -> Path:
    """Write a fixture story file into root/docs/features/F-999-fixture/stories/."""
    sid = name.split("-")[0] + "-" + name.split("-")[1]
    stories_dir = root / "docs" / "features" / "F-999-fixture" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    story_path = stories_dir / f"{name}.md"
    story_path.write_text(
        STORY_TEMPLATE.format(sid=sid, status=status,
                              requirements=requirements, targets=targets),
        encoding="utf-8")
    return story_path


def run_plan_check(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    """Run plan_check.py via subprocess and return the completed process."""
    return subprocess.run(
        [sys.executable, str(PLAN_CHECK), *args],
        capture_output=True, text=True, cwd=str(cwd))


def run_check_on(root: Path, *extra: str) -> subprocess.CompletedProcess:
    """Full scan of the story tree under root (cwd=root)."""
    return run_plan_check(root, "--root", str(root), *extra)


def test_clean_story_passes(tmp_path):
    """A clean open story -> PASS, empty problems, empty conflict candidates."""
    write_story(tmp_path, "01-01-clean-story",
                targets="- Create `scripts/clean_new.py`.")
    result = run_check_on(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] == "PASS"
    assert output["problems"] == []
    assert output["conflict_candidates"] == []


def test_ghost_reference_fails(tmp_path):
    """A story extending a nonexistent file -> ghost-reference problem, exit 1."""
    write_story(tmp_path, "01-02-ghost-story",
                targets="- Extend `tests/test_ghost_really_missing.py` with a "
                        "regression test.")
    result = run_check_on(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] == "FAIL"
    ghosts = [p for p in output["problems"] if p["kind"] == "ghost-reference"]
    assert ghosts, output
    assert ghosts[0]["story"] == "01-02"
    assert "tests/test_ghost_really_missing.py" in ghosts[0]["detail"]
    for problem in output["problems"]:
        assert set(problem) == {"story", "kind", "detail"}


def test_conflict_candidates_reported(tmp_path):
    """Two open stories touching the same file -> conflict candidate, exit 0."""
    write_story(tmp_path, "02-01-conflict-a",
                targets="- Update `scripts/shared_conflict.py`.")
    write_story(tmp_path, "02-02-conflict-b",
                targets="- Update `scripts/shared_conflict.py`.")
    result = run_check_on(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] == "PASS"
    assert output["problems"] == []
    assert output["conflict_candidates"] == [
        {"file": "scripts/shared_conflict.py", "stories": ["02-01", "02-02"]}]
    for candidate in output["conflict_candidates"]:
        assert set(candidate) == {"file", "stories"}


def test_clarification_marker_fails(tmp_path):
    """A plain [NEEDS CLARIFICATION] marker in an open story -> exit 1."""
    write_story(tmp_path, "03-01-marker-story",
                requirements="1. Do the thing. [NEEDS CLARIFICATION: which "
                             "module owns the helper?]")
    result = run_check_on(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] == "FAIL"
    kinds = [p["kind"] for p in output["problems"]]
    assert "clarification-marker" in kinds


def test_missing_section_fails(tmp_path):
    """An empty required section (Requirements) -> exit 1."""
    write_story(tmp_path, "04-01-empty-reqs", requirements="")
    result = run_check_on(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] == "FAIL"
    missing = [p for p in output["problems"] if p["kind"] == "missing-section"]
    assert missing, output
    assert "Requirements" in missing[0]["detail"]


def test_done_stories_skipped(tmp_path):
    """A Done story with a ghost reference is historical record -> not checked."""
    write_story(tmp_path, "05-01-done-story", status="Done",
                targets="- Extend `tests/test_done_ghost.py` with coverage.")
    result = run_check_on(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["problems"] == []
    assert output["conflict_candidates"] == []


def test_single_story_mode(tmp_path):
    """--story checks exactly one story; other open stories' problems are ignored."""
    ghost_path = write_story(tmp_path, "06-01-ghost-story",
                             targets="- Extend `tests/test_single_ghost.py` "
                                     "with coverage.")
    clean_path = write_story(tmp_path, "06-02-clean-story",
                             targets="- Create `scripts/single_new.py`.")
    # Full scan: the ghost story fails the run.
    full = run_check_on(tmp_path)
    assert full.returncode == 1, full.stdout + full.stderr
    # Single-story mode on the CLEAN story: exit 0, no problems.
    single_clean = run_plan_check(tmp_path, "--root", str(tmp_path),
                                  "--story", str(clean_path))
    assert single_clean.returncode == 0, single_clean.stdout + single_clean.stderr
    clean_output = json.loads(single_clean.stdout)
    assert clean_output["result"] == "PASS"
    assert clean_output["problems"] == []
    # Single-story mode on the GHOST story: exit 1, problems name only that story.
    single_ghost = run_plan_check(tmp_path, "--root", str(tmp_path),
                                  "--story", str(ghost_path))
    assert single_ghost.returncode == 1, single_ghost.stdout + single_ghost.stderr
    ghost_output = json.loads(single_ghost.stdout)
    assert ghost_output["problems"]
    assert all(p["story"] == "06-01" for p in ghost_output["problems"])


def test_sequenced_cross_reference_warns(tmp_path):
    """Audit fix case: open story A creates a path, open story B extends it ->
    sequenced-reference WARN (exit unchanged), never a ghost-FAIL."""
    write_story(tmp_path, "07-01-create-a",
                targets="- Create `scripts/seq_shared.py`.")
    write_story(tmp_path, "07-02-extend-b",
                targets="- Extend `scripts/seq_shared.py` with the new helper.")
    result = run_check_on(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] == "PASS"
    sequenced = [p for p in output["problems"]
                 if p["kind"] == "sequenced-reference"]
    assert sequenced, output
    assert sequenced[0]["story"] == "07-02"
    assert "scripts/seq_shared.py" in sequenced[0]["detail"]
    assert not any(p["kind"] == "ghost-reference" for p in output["problems"])
    # Both stories touch the same file -> also a conflict candidate (WARN).
    assert {"file": "scripts/seq_shared.py",
            "stories": ["07-01", "07-02"]} in output["conflict_candidates"]


def test_f030_self_check_each_story_exit_zero():
    """Self-check: plan_check parses THIS repo's real F-030 story files without
    error and each open story yields exit 0 (WARN semantics only: sequenced
    references and conflict candidates must not fail the run)."""
    stories_dir = REPO_ROOT / "docs" / "features" / "F-030-process-driver" / "stories"
    story_files = sorted(stories_dir.glob("*.md"))
    # Count-agnostic on purpose: new stories may be added to the feature over
    # time (30-06 was added after this test was written); the invariant is
    # "every story in the dir parses cleanly", not a fixed count.
    assert len(story_files) >= 5, [f.name for f in story_files]
    for story_file in story_files:
        result = run_plan_check(REPO_ROOT, "--story", str(story_file))
        assert result.returncode == 0, (
            f"{story_file.name}: exit {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}")
        output = json.loads(result.stdout)
        assert set(output) >= {"result", "problems", "conflict_candidates"}
        for problem in output["problems"]:
            assert set(problem) == {"story", "kind", "detail"}
            assert problem["kind"] in {
                "ghost-reference", "sequenced-reference",
                "clarification-marker", "missing-section"}


def test_missing_status_line_flagged(tmp_path):
    """A non-Done story file without a Status: line -> missing-status-line problem."""
    # Write a story template without the Status: line
    stories_dir = tmp_path / "docs" / "features" / "F-999-fixture" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    story_path = stories_dir / "08-01-no-status.md"
    story_text = """# Story 08-01 — fixture story

Feature: Fixture (F-999)

## Codebase Snapshot

- `docs/features/_story_template.md` — the story skeleton used by create_story.py.

## Context / Purpose

Fixture purpose text for the plan_check test suite.

## Requirements

1. Do the fixture thing.

## Developer Targets (exactly, no more / no less)

- Create `scripts/fixture_new.py`.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- Fixture criterion verified.

## Test criteria (must exist BEFORE implementation)

- `tests/test_fixture.py::test_fixture_case`

"""
    story_path.write_text(story_text, encoding="utf-8")
    result = run_check_on(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] == "FAIL"
    missing_status = [p for p in output["problems"] if p["kind"] == "missing-status-line"]
    assert missing_status, output
    assert missing_status[0]["story"] == "08-01"
    for problem in output["problems"]:
        assert set(problem) == {"story", "kind", "detail"}


def test_done_story_missing_status_not_flagged(tmp_path):
    """A Done story without Status: line is silently skipped (no problem)."""
    stories_dir = tmp_path / "docs" / "features" / "F-999-fixture" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    story_path = stories_dir / "09-01-done-no-status.md"
    story_text = """# Story 09-01 — fixture story

Status: Done
Feature: Fixture (F-999)

## Codebase Snapshot

- `docs/features/_story_template.md` — the story skeleton used by create_story.py.

## Context / Purpose

Fixture purpose text for the plan_check test suite.

## Requirements

1. Do the fixture thing.

## Developer Targets (exactly, no more / no less)

- Create `scripts/fixture_new.py`.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- Fixture criterion verified.

## Test criteria (must exist BEFORE implementation)

- `tests/test_fixture.py::test_fixture_case`

"""
    story_path.write_text(story_text, encoding="utf-8")
    result = run_check_on(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] == "PASS"
    assert output["problems"] == []


def test_duplicate_story_id_flagged(tmp_path):
    """Two files with the same numeric ID prefix (33-01-*.md) -> duplicate-story-id problem."""
    stories_dir = tmp_path / "docs" / "features" / "F-999-fixture" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    
    # Write two stories with the same ID prefix
    story1_path = stories_dir / "10-01-foo.md"
    story2_path = stories_dir / "10-01-bar.md"
    
    story_template = """# Story {sid} — fixture story

Status: Planned
Feature: Fixture (F-999)

## Codebase Snapshot

- `docs/features/_story_template.md` — the story skeleton.

## Context / Purpose

Fixture purpose text for the plan_check test suite.

## Requirements

1. Do the fixture thing.

## Developer Targets (exactly, no more / no less)

- Create `scripts/fixture_new.py`.

## Acceptance criteria (checked by qa-manager)

- Fixture criterion verified.

## Test criteria (must exist BEFORE implementation)

- `tests/test_fixture.py::test_fixture_case`

"""
    
    story1_path.write_text(story_template.format(sid="10-01"), encoding="utf-8")
    story2_path.write_text(story_template.format(sid="10-01"), encoding="utf-8")
    
    result = run_check_on(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] == "FAIL"
    duplicates = [p for p in output["problems"] if p["kind"] == "duplicate-story-id"]
    assert duplicates, output
    # The duplicate-story-id problem should list both paths
    dup_detail = duplicates[0]["detail"]
    assert "10-01-foo.md" in dup_detail
    assert "10-01-bar.md" in dup_detail


def test_since_flag_skips_older_stories(tmp_path):
    """With --since 33-01, stories with ID < 33-01 skip missing-section checks but are still parsed."""
    stories_dir = tmp_path / "docs" / "features" / "F-999-fixture" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    
    # Create an old story (32-05) with missing requirements section
    old_story = stories_dir / "32-05-old-story.md"
    old_text = """# Story 32-05 — old fixture story

Status: Planned
Feature: Fixture (F-999)

## Codebase Snapshot

- `docs/features/_story_template.md`.

## Context / Purpose

Old story purpose.

## Developer Targets (exactly, no more / no less)

- Create `scripts/old_fixture.py`.

## Acceptance criteria (checked by qa-manager)

- Fixture criterion verified.

## Test criteria (must exist BEFORE implementation)

- `tests/test_fixture.py::test_fixture_case`

"""
    old_story.write_text(old_text, encoding="utf-8")
    
    # Create a new story (33-05) with missing requirements section
    new_story = stories_dir / "33-05-new-story.md"
    new_text = """# Story 33-05 — new fixture story

Status: Planned
Feature: Fixture (F-999)

## Codebase Snapshot

- `docs/features/_story_template.md`.

## Context / Purpose

New story purpose.

## Developer Targets (exactly, no more / no less)

- Create `scripts/new_fixture.py`.

## Acceptance criteria (checked by qa-manager)

- Fixture criterion verified.

## Test criteria (must exist BEFORE implementation)

- `tests/test_fixture.py::test_fixture_case`

"""
    new_story.write_text(new_text, encoding="utf-8")
    
    # Full scan: both stories should fail (missing Requirements)
    full_result = run_check_on(tmp_path)
    assert full_result.returncode == 1, full_result.stdout + full_result.stderr
    full_output = json.loads(full_result.stdout)
    missing_full = [p for p in full_output["problems"] if p["kind"] == "missing-section"]
    assert len(missing_full) == 2, f"Expected 2 missing-section problems, got {len(missing_full)}: {missing_full}"
    assert any(p["story"] == "32-05" for p in missing_full), "32-05 should have missing-section"
    assert any(p["story"] == "33-05" for p in missing_full), "33-05 should have missing-section"
    
    # With --since 33-01, only 33-05 should be checked for missing-section (32-05 is older)
    since_result = run_plan_check(tmp_path, "--root", str(tmp_path), "--since", "33-01")
    assert since_result.returncode == 1, since_result.stdout + since_result.stderr
    since_output = json.loads(since_result.stdout)
    missing_since = [p for p in since_output["problems"] if p["kind"] == "missing-section"]
    # Only 33-05 should be checked; 32-05 should be skipped
    assert all(p["story"] != "32-05" for p in missing_since), \
        f"32-05 should be skipped with --since 33-01, but found in: {missing_since}"
    assert any(p["story"] == "33-05" for p in missing_since), \
        f"33-05 should still be checked with --since 33-01"


def test_since_flag_does_not_skip_ghost_refs(tmp_path):
    """With --since, ghost-ref and conflict-candidate checks still scan all stories."""
    stories_dir = tmp_path / "docs" / "features" / "F-999-fixture" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    
    # Create an old story (32-05) with a ghost reference
    old_ghost = stories_dir / "32-05-old-ghost.md"
    old_text = """# Story 32-05 — old with ghost

Status: Planned
Feature: Fixture (F-999)

## Codebase Snapshot

- `docs/features/_story_template.md`.

## Context / Purpose

Old story purpose.

## Requirements

1. Do the thing.

## Developer Targets (exactly, no more / no less)

- Extend `tests/test_ghost_really_old.py` with coverage.

## Acceptance criteria (checked by qa-manager)

- Fixture criterion verified.

## Test criteria (must exist BEFORE implementation)

- `tests/test_fixture.py::test_fixture_case`

"""
    old_ghost.write_text(old_text, encoding="utf-8")
    
    # Full scan should detect the ghost-ref
    full_result = run_check_on(tmp_path)
    assert full_result.returncode == 1, full_result.stdout + full_result.stderr
    full_output = json.loads(full_result.stdout)
    ghosts_full = [p for p in full_output["problems"] if p["kind"] == "ghost-reference"]
    assert ghosts_full, f"Expected ghost-reference in full scan, got: {full_output['problems']}"
    
    # With --since 33-01, the ghost-ref should STILL be reported (ghost-refs are NOT skipped by --since)
    since_result = run_plan_check(tmp_path, "--root", str(tmp_path), "--since", "33-01")
    assert since_result.returncode == 1, since_result.stdout + since_result.stderr
    since_output = json.loads(since_result.stdout)
    ghosts_since = [p for p in since_output["problems"] if p["kind"] == "ghost-reference"]
    assert ghosts_since, \
        f"Expected ghost-reference to be reported even with --since 33-01, got: {since_output['problems']}"
    assert any(p["story"] == "32-05" for p in ghosts_since), \
        "32-05 ghost-ref should be reported even though 32-05 < 33-01"


def test_full_scan_json_contract():
    """Full scan of the real repo story tree: valid JSON contract regardless of
    findings (problems may legitimately exist in other features' open stories)."""
    result = run_plan_check(REPO_ROOT)
    assert result.returncode in (0, 1), result.stdout + result.stderr
    output = json.loads(result.stdout)
    assert output["result"] in ("PASS", "FAIL")
    assert isinstance(output["problems"], list)
    assert isinstance(output["conflict_candidates"], list)
    for problem in output["problems"]:
        assert set(problem) == {"story", "kind", "detail"}
    for candidate in output["conflict_candidates"]:
        assert set(candidate) == {"file", "stories"}
        assert isinstance(candidate["stories"], list)
        assert len(candidate["stories"]) >= 2
