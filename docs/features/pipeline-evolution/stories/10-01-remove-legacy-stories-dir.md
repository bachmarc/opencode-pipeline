# Story 10-01 — Remove legacy docs/stories/ directory

Status: Planned
Feature: pipeline-evolution (F-004)

## Context / Purpose

When the feature hierarchy was introduced (Story 06-01), story files were migrated from
`docs/stories/` to `docs/features/<name>/stories/`. The old `docs/stories/` directory was
kept with just `_template.md` for backward compatibility. Since then, the canonical template
lives at `docs/features/_story_template.md` (identical content). The old directory is now
dead weight — references to it in code, tests, and docs create confusion about the source
of truth.

## Requirements

- `docs/stories/` directory no longer exists
- All references to `docs/stories/` in code, tests, scripts, and docs are removed or updated
- No test regressions — all existing tests pass

## Developer Targets (exactly, no more / no less)

- **Delete** `docs/stories/_template.md` and the `docs/stories/` directory
- **`STORIES.md`** line 4: change `docs/stories/_template.md` → `docs/features/_story_template.md`
- **`tests/test_templates.py`**: remove `test_story_templates_in_sync` test (no longer two locations to sync)
- **`tests/test_feature_hierarchy.py`**: remove the backward-compat allowance for `docs/stories/_template.md` in `test_story_files_in_features` (the check that old `docs/stories/` only has `_template.md`)
- **`scripts/worktree_setup.py`**: remove the backward-compat fallback that searches `docs/stories/<id>-*.md`
- **`tests/test_check_scripts.py`**: update the embedded string reference from `docs/stories/<phase>-<id>-<slug>.md` to `docs/features/<name>/stories/<id>-<slug>.md`

## Acceptance criteria (checked by qa-manager)

- `docs/stories/` directory does not exist
- `rg "docs/stories"` returns zero matches across the entire repo
- All pytest tests pass (`pytest` green)
- No functional regression in `scripts/worktree_setup.py` (still finds stories in `docs/features/*/stories/`)

## Test criteria (must exist BEFORE implementation)

- `tests/test_feature_hierarchy.py::test_no_legacy_stories_dir` — asserts `docs/stories/` directory does not exist
- `tests/test_feature_hierarchy.py::test_story_files_in_features` — existing test, now stricter (no backward-compat allowance)
- `tests/test_templates.py` — `test_story_templates_in_sync` removed; remaining template tests still pass
- `pytest` full suite green
