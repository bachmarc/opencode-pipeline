"""CLI tests for scripts/driver.py (Story 30-01).

Runs the real CLI via subprocess against a fixture temp repo: `.pipeline/`
populated (qa-state verdicts, intent.json), fake `process.json` profile and
story files with `Status:` lines. No external systems, no fakes needed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "driver.py"

STALE_TIMESTAMP = "2020-01-01T00:00:00+00:00"
FRESH_TIMESTAMP = "2026-10-30T00:00:00+00:00"


def _write_story(repo: Path, name: str, status: str) -> None:
    """Write a story file with a Status: line (docs/features/F-TEST/stories/)."""
    stories_dir = repo / "docs" / "features" / "F-TEST" / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)
    (stories_dir / name).write_text(
        f"# Story {name}\n\nStatus: {status}\nFeature: F-TEST\n\n"
        "## Requirements\n\n- something\n",
        encoding="utf-8",
    )


def _write_verdict(repo: Path, story_id: str, verdict: str) -> None:
    """Write a QA verdict file (.pipeline/qa-state/<story_id>.json)."""
    qa_dir = repo / ".pipeline" / "qa-state"
    qa_dir.mkdir(parents=True, exist_ok=True)
    (qa_dir / f"{story_id}.json").write_text(
        json.dumps({"verdicts": [{"verdict": verdict, "timestamp": FRESH_TIMESTAMP}]}),
        encoding="utf-8",
    )


def make_fixture_repo(tmp_path: Path) -> Path:
    """Fixture temp repo: 1 stale open intent, 1 story with QA PASS not merged,
    1 story FAIL, 1 story dev-done without a verdict."""
    repo = tmp_path / "repo"
    pipeline = repo / ".pipeline"
    pipeline.mkdir(parents=True)

    # Story statuses come from the Status: lines of the story files.
    _write_story(repo, "99-01-no-verdict.md", "In Progress")  # -> spawn-qa
    _write_story(repo, "99-02-pass-open.md", "In Progress")  # -> merge-candidate
    _write_story(repo, "99-03-fail.md", "Planned")  # -> spawn-dev

    _write_verdict(repo, "99-02", "PASS")
    _write_verdict(repo, "99-03", "FAIL")

    (pipeline / "intent.json").write_text(
        json.dumps(
            {
                "intents": [
                    {
                        "story_id": "99-01",
                        "agent": "developer",
                        "step": "writing tests (red-first)",
                        "started_at": STALE_TIMESTAMP,
                        "done": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return repo


def run_driver(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run driver.py and return the completed process."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# test_cli_validate_pass_fail
# ---------------------------------------------------------------------------


def test_cli_validate_pass_fail(tmp_path: Path) -> None:
    """Valid fixture profile -> exit 0 {"result": "PASS"};
    missing `workflow` -> exit 1 with the key name in the output."""
    repo = make_fixture_repo(tmp_path)
    profile = repo / ".pipeline" / "process.json"

    profile.write_text(
        json.dumps({"workflow": "default", "test_strategy": "unit-fake"}), encoding="utf-8"
    )
    result = run_driver("validate", "--profile", str(profile), cwd=repo)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert json.loads(result.stdout)["result"] == "PASS"

    profile.write_text(json.dumps({"test_strategy": "unit-fake"}), encoding="utf-8")
    result = run_driver("validate", "--profile", str(profile), cwd=repo)
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["result"] == "FAIL"
    assert any("workflow" in err for err in data["errors"]), data


def test_cli_validate_unknown_keys_warning(tmp_path: Path) -> None:
    """Unknown profile keys -> warning on stdout, exit 0."""
    repo = make_fixture_repo(tmp_path)
    profile = repo / ".pipeline" / "process.json"
    profile.write_text(
        json.dumps({"workflow": "custom", "test_strategy": "hybrid", "escalation_threshold": 3}),
        encoding="utf-8",
    )
    result = run_driver("validate", "--profile", str(profile), cwd=repo)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["result"] == "PASS"
    assert "warnings" in data and any("escalation_threshold" in w for w in data["warnings"])


# ---------------------------------------------------------------------------
# test_cli_next_fixture_repo
# ---------------------------------------------------------------------------


def test_cli_next_fixture_repo(tmp_path: Path) -> None:
    """Fixture repo with .pipeline/ populated produces the 4-action JSON on stdout."""
    repo = make_fixture_repo(tmp_path)
    repo.joinpath(".pipeline", "process.json").write_text(
        json.dumps({"workflow": "default", "test_strategy": "unit-fake"}), encoding="utf-8"
    )

    result = run_driver("next", cwd=repo)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    actions = json.loads(result.stdout)
    assert isinstance(actions, list)
    assert [a["kind"] for a in actions] == [
        "intent-reminder",
        "spawn-qa",
        "merge-candidate",
        "spawn-dev",
    ]
    by_kind = {a["kind"]: a for a in actions}
    assert by_kind["intent-reminder"]["story_id"] == "99-01"
    assert by_kind["spawn-qa"]["story_id"] == "99-01"
    assert by_kind["merge-candidate"]["story_id"] == "99-02"
    assert by_kind["spawn-dev"]["story_id"] == "99-03"
    for action in actions:
        assert "reason" in action and isinstance(action["reason"], str)


def test_cli_next_status_from_story_files_not_stories_md(tmp_path: Path) -> None:
    """Story statuses are parsed from `Status:` lines of docs/features/*/stories/*.md —
    NOT from the STORIES.md markdown table (which lies in this fixture)."""
    repo = make_fixture_repo(tmp_path)
    (repo / "STORIES.md").write_text(
        "| Story | Title | Status | Feature |\n| 99-01 | x | **Done** | F-TEST |\n",
        encoding="utf-8",
    )

    result = run_driver("next", cwd=repo)
    assert result.returncode == 0
    actions = json.loads(result.stdout)
    kinds = [a["kind"] for a in actions]
    # STORIES.md claims 99-01 is Done — but the story file says "In Progress",
    # so spawn-qa for 99-01 must still be emitted.
    assert "spawn-qa" in kinds


def test_cli_next_default_profile_when_missing(tmp_path: Path) -> None:
    """No process.json -> built-in default profile, next still works."""
    repo = make_fixture_repo(tmp_path)
    result = run_driver("next", cwd=repo)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    actions = json.loads(result.stdout)
    assert [a["kind"] for a in actions] == [
        "intent-reminder",
        "spawn-qa",
        "merge-candidate",
        "spawn-dev",
    ]
