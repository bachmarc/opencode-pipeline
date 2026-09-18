"""Tests for dev-start guard — warns when developer/qa-manager spawned without story."""

import re
from pathlib import Path


def test_dev_start_guard_file_exists():
    """plugins/guards/dev-start-guard.ts exists."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    assert guard_file.exists(), f"Guard file not found at {guard_file}"


def test_dev_start_guard_has_story_regex():
    """plugins/guards/dev-start-guard.ts contains story ID regex pattern."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    content = guard_file.read_text()

    # Check for the story ID regex pattern \d{2}-\d{2}
    assert r"\d{2}-\d{2}" in content or "\\d{2}-\\d{2}" in content, \
        "Story ID regex pattern (\\d{2}-\\d{2}) not found in guard file"


def test_dev_start_guard_reads_stories():
    """plugins/guards/dev-start-guard.ts contains reference to STORIES.md."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    content = guard_file.read_text()

    assert "STORIES.md" in content, "STORIES.md reference not found in guard file"


def test_plugin_imports_dev_start_guard():
    """plugins/pipeline-enforcement.ts imports dev-start-guard."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()

    assert "dev-start-guard" in content, "dev-start-guard import not found in pipeline-enforcement.ts"


def test_dev_start_guard_strips_slug():
    """plugins/guards/dev-start-guard.ts normalizes row IDs (strips slug) before pattern test.

    STORIES.md row IDs carry slugs (e.g. '12-01-qa-config-contract'); the guard must
    normalize via first two dash segments before testing against XX-YY / RETRO-XX.
    """
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "dev-start-guard.ts"
    content = guard_file.read_text()

    assert '.split("-")' in content, \
        "Slug normalization (.split(\"-\")) not found in guard file"
    assert ".slice(0, 2)" in content, \
        "Slug normalization (.slice(0, 2)) not found in guard file"


def test_dev_start_guard_stories_rows_with_slugs():
    """Every STORIES.md table row ID normalizes to XX-YY / RETRO-XX pattern.

    Documents the invariant the guard relies on: applying the same normalization
    as the guard (first two dash segments joined by '-') turns each real row ID
    (e.g. '12-01-qa-config-contract') into a bare ID matching ^\\d{2}-\\d{2}$ or
    ^RETRO-\\d{2}$.
    """
    repo_root = Path(__file__).resolve().parent.parent
    stories_file = repo_root / "STORIES.md"
    pattern = re.compile(r"^(\d{2}-\d{2}|RETRO-\d{2})$")

    checked = 0
    with stories_file.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.startswith("|") or "---" in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue
            raw_id = parts[1]
            # Skip header row (first cell "Story") — not a data row.
            # Strip markdown bold markers (legacy rows like **06-01-...**).
            raw_id = raw_id.strip().strip("*")
            if not raw_id or raw_id == "Story":
                continue
            story_id = "-".join(raw_id.split("-")[:2])
            assert pattern.match(story_id), (
                f"Row ID {raw_id!r} does not normalize to XX-YY / RETRO-XX "
                f"(got {story_id!r})"
            )
            checked += 1

    assert checked > 0, "No STORIES.md table rows found to check"