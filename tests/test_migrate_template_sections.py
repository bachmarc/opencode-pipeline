"""Tests for migrate_template_sections.py — deterministic template migration.

Runs scripts/migrate_template_sections.py via subprocess against tmp_path
project AGENTS.md files (no real projects touched). The template is resolved
by the script itself relative to its own repo root, so tests run with
cwd=tmp_path to prove cwd-independence.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
MIGRATE_SCRIPT = SCRIPTS_DIR / "migrate_template_sections.py"
CONSTANCY_SCRIPT = SCRIPTS_DIR / "check_template_constancy.py"
TEMPLATE_PATH = REPO_ROOT / "templates" / "AGENTS.md"

CONSTANT_HEADINGS = [
    "## Workflow",
    "## Git conventions",
    "## Languages",
    "## Prohibitions",
]

# Old (pre-12-08) wording that the 12-08 template change removed.
NEW_WORKFLOW_LINE = (
    "   Write tests first, the project's configured test suite must be green."
)
OLD_WORKFLOW_LINE = "   Write tests first, `pytest` must be green."
NEW_GIT_LINE = (
    "   symbols: <changed export symbols> | breaks: <none|breaking> "
    "| affects: <dependent files> | tests: <test suite result>"
)
OLD_GIT_LINE = (
    "   symbols: <changed export symbols> | breaks: <none|breaking> "
    "| affects: <dependent files> | tests: <pytest result>"
)


def _run_migrate(target: Path, tmp_path: Path) -> subprocess.CompletedProcess:
    """Run migrate_template_sections.py with cwd=tmp_path (not the repo root)."""
    return subprocess.run(
        [sys.executable, str(MIGRATE_SCRIPT), str(target)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        check=False,
    )


def _run_constancy(target: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CONSTANCY_SCRIPT), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )


def _block_ranges(lines: List[str]) -> List[tuple]:
    """(start, end) ranges: preamble block plus one block per '## ' heading."""
    starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    bounds = [0] + starts
    ranges = []
    for idx, start in enumerate(bounds):
        end = bounds[idx + 1] if idx + 1 < len(bounds) else len(lines)
        ranges.append((start, end))
    return ranges


def _strip_sections(content: str, headings: List[str]) -> str:
    """Remove the given '## ' sections (heading up to next '## ' heading)."""
    lines = content.split("\n")
    keep: List[str] = []
    skip = False
    for line in lines:
        if line.startswith("## "):
            skip = line.strip() in headings
        if not skip:
            keep.append(line)
    return "\n".join(keep)


def _write_old_project_agents(tmp_path: Path, name: str = "AGENTS.md") -> Path:
    """Project AGENTS.md with OLD constant-section wording + custom sections."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert NEW_WORKFLOW_LINE in template, "template changed: workflow line missing"
    assert NEW_GIT_LINE in template, "template changed: git-conventions line missing"
    old = template.replace(NEW_WORKFLOW_LINE, OLD_WORKFLOW_LINE)
    old = old.replace(NEW_GIT_LINE, OLD_GIT_LINE)
    assert "`pytest` must be green" in old, "old workflow wording not applied"
    assert "tests: <pytest result>" in old, "old git-conventions wording not applied"
    old = old.replace(
        "# AGENTS.md — <Project name>", "# AGENTS.md — Legacy Custom Project"
    )
    assert "## This project" in old, "custom project section missing"
    path = tmp_path / name
    path.write_text(old, encoding="utf-8")
    return path


def test_migrate_old_project_agents(tmp_path):
    """Old-wording project file: migration replaces sections, constancy PASSes,
    project-specific content stays byte-identical."""
    target = _write_old_project_agents(tmp_path)
    before = target.read_text(encoding="utf-8")

    result = _run_migrate(target, tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload = json.loads(result.stdout)
    assert payload["migrated"] is True
    assert "Workflow" in payload["sections"]
    assert "Git conventions" in payload["sections"]

    # Constancy check passes the migrated file.
    check = _run_constancy(target)
    assert check.returncode == 0, f"constancy output: {check.stdout}"
    assert json.loads(check.stdout)["result"] == "PASS"

    # Project-specific content outside the constant sections is byte-identical.
    after = target.read_text(encoding="utf-8")
    assert _strip_sections(after, CONSTANT_HEADINGS) == _strip_sections(
        before, CONSTANT_HEADINGS
    )
    assert "# AGENTS.md — Legacy Custom Project" in after
    assert "## This project" in after


def test_migrate_idempotent(tmp_path):
    """Second run on an already-migrated file changes nothing."""
    target = _write_old_project_agents(tmp_path)
    first = _run_migrate(target, tmp_path)
    assert first.returncode == 0
    assert json.loads(first.stdout)["migrated"] is True

    snapshot = target.read_bytes()
    second = _run_migrate(target, tmp_path)
    assert second.returncode == 0, f"stderr: {second.stderr}"
    payload = json.loads(second.stdout)
    assert payload["migrated"] is False
    assert payload["reason"] == "already current"
    assert target.read_bytes() == snapshot


def test_migrate_missing_file(tmp_path):
    """Nonexistent input path: exit 1 with JSON error."""
    missing = tmp_path / "does-not-exist" / "AGENTS.md"
    result = _run_migrate(missing, tmp_path)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert "error" in payload


def test_migrate_no_sections(tmp_path):
    """File without any constant-section heading: exit 1, file untouched."""
    target = tmp_path / "AGENTS.md"
    original = "# Notes\n\n## Random\n\nJust some plain markdown content.\n"
    target.write_text(original, encoding="utf-8")

    result = _run_migrate(target, tmp_path)
    assert result.returncode == 1
    assert "no constant sections found" in result.stdout
    assert target.read_text(encoding="utf-8") == original


def test_migrate_inserts_missing_section(tmp_path):
    """File with only Workflow + Git sections: Languages/Prohibitions are
    inserted before '## References'; constancy PASSes afterwards."""
    target = _write_old_project_agents(tmp_path)
    before = target.read_text(encoding="utf-8")
    removed = _strip_sections(
        before, ["## Languages", "## Prohibitions"]
    )
    target.write_text(removed, encoding="utf-8")
    assert "## Languages" not in target.read_text(encoding="utf-8")

    result = _run_migrate(target, tmp_path)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload = json.loads(result.stdout)
    assert payload["migrated"] is True
    assert "Languages" in payload["sections"]
    assert "Prohibitions" in payload["sections"]

    after = target.read_text(encoding="utf-8")
    # Inserted before '## References' (which the template-derived file has).
    assert after.index("## Languages") < after.index("## References")
    assert after.index("## Prohibitions") < after.index("## References")

    check = _run_constancy(target)
    assert check.returncode == 0, f"constancy output: {check.stdout}"
    assert json.loads(check.stdout)["result"] == "PASS"

    # Content outside the constant sections is still byte-identical.
    assert _strip_sections(after, CONSTANT_HEADINGS) == _strip_sections(
        removed, CONSTANT_HEADINGS
    )