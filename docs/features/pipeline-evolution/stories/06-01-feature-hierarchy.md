# Story 06-01 — Feature-hierarchy file structure

Status: Done
Feature: pipeline-evolution (F-004)

## Context / Purpose

Replace the flat `STORIES.md` table with a hierarchical feature → story structure in the
file system. This is the foundation for all subsequent stories (claim, recovery, status
scripts all depend on this layout).

## Requirements

After this story, the repo has `docs/features/` with the new directory layout, a
`FEATURES.md` index, and `feature.md` + `stories/` sub-directories. Existing stories
are migrated into the new structure.

## Developer Targets (exactly, no more / no less)

- Create `docs/features/` directory
- Create `FEATURES.md` at repo root (top-level index, same format as Design §9)
- Migrate existing `docs/stories/*.md` files into appropriate feature sub-directories
  (group by phase: retro, foundation, i18n, docs — each becomes a feature)
- Each feature gets a `feature.md` with YAML-like header (id, title, status, owner, req)
- Old `STORIES.md` is replaced by `FEATURES.md` (keep `STORIES.md` as redirect/symlink
  or remove with a note in the commit)
- Update `docs/stories/_template.md` → `docs/features/_story_template.md`

## Acceptance criteria (checked by qa-manager)

- `FEATURES.md` exists at repo root and contains a Markdown table with all features
- Each feature has `docs/features/<name>/feature.md` with required fields
- Each feature has `docs/features/<name>/stories/` with migrated story files
- No story files remain in `docs/stories/` (except `_template.md` moved to new location)
- All existing story content is preserved (no data loss)
- `_story_template.md` exists under `docs/features/`

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_feature_hierarchy.py::test_features_md_exists` — `FEATURES.md` exists at repo root
- `tests/test_feature_hierarchy.py::test_features_md_has_table` — contains Markdown table with required columns (Feature, Title, Status, Owner, Stories, Traceability)
- `tests/test_feature_hierarchy.py::test_feature_dirs_exist` — every feature listed in `FEATURES.md` has a corresponding `docs/features/<name>/` directory
- `tests/test_feature_hierarchy.py::test_feature_md_fields` — each `feature.md` contains required fields (id, title, status, req)
- `tests/test_feature_hierarchy.py::test_story_files_in_features` — story files exist under `docs/features/<name>/stories/`, not under `docs/stories/`
- `tests/test_feature_hierarchy.py::test_story_template_exists` — `docs/features/_story_template.md` exists
