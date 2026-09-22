# Story 15-00 — Numbered Feature Folders

Status: Planned
Feature: living-code-docs (F-011)

## Context / Purpose

Feature folders under `docs/features/` currently use only the slug name (e.g., `foundation/`,
`pipeline-enforcement/`). The feature ID (F-001, F-007) is only visible inside the
`feature.md` frontmatter. When browsing the filesystem, there is no way to see which
number belongs to which feature without opening each file.

By prefixing folder names with the feature ID (e.g., `F-001-foundation/`,
`F-007-pipeline-enforcement/`), the mapping is immediately visible in directory listings
and file paths. This is a mechanical rename — no logic changes, no story-file content
changes (the `Feature:` line in stories keeps the human-readable name).

## Requirements

1. All 11 existing feature folders must be renamed from `<slug>/` to `F-<ID>-<slug>/`.
2. The new F-011 folder must already use the new convention (done during planning).
3. `scripts/create_retro_stories.py` must use the new folder name `F-RETRO-retro`.
4. `tests/test_create_retro_stories.py` must reference the new folder name.
5. All existing tests must pass after the rename (scripts discover folders dynamically).
6. Story files' `Feature:` lines remain unchanged (human-readable name, not folder path).

## Developer Targets (exactly, no more / no less)

- `git mv` the 11 existing folders:
  - `docs/features/retro/` → `docs/features/F-RETRO-retro/`
  - `docs/features/foundation/` → `docs/features/F-001-foundation/`
  - `docs/features/i18n/` → `docs/features/F-002-i18n/`
  - `docs/features/docs/` → `docs/features/F-003-docs/`
  - `docs/features/pipeline-evolution/` → `docs/features/F-004-pipeline-evolution/`
  - `docs/features/doc-model-reform/` → `docs/features/F-005-doc-model-reform/`
  - `docs/features/doc-model-migration/` → `docs/features/F-006-doc-model-migration/`
  - `docs/features/pipeline-enforcement/` → `docs/features/F-007-pipeline-enforcement/`
  - `docs/features/polyglot-qa/` → `docs/features/F-008-polyglot-qa/`
  - `docs/features/project-migration/` → `docs/features/F-009-project-migration/`
  - `docs/features/eliminate-derived-docs/` → `docs/features/F-010-eliminate-derived-docs/`
  (F-011-living-code-docs already uses the new convention)

- `scripts/create_retro_stories.py`: Change hardcoded `"retro"` folder name to
  `"F-RETRO-retro"` (line ~53 and line ~144 in Feature: output).

- `tests/test_create_retro_stories.py`: Update all `"retro"` path references to
  `"F-RETRO-retro"` (~7 occurrences).

- Do NOT change `Feature:` lines in story files.
- Do NOT change STORIES.md traceability column (it shows logical name, not path).
- Update docstrings/module headers in changed files.

## Acceptance criteria (checked by qa-manager)

- All 12 feature folders use the `F-<ID>-<slug>/` naming convention
- No folder with the old naming convention exists under `docs/features/`
- `scripts/create_retro_stories.py` references `F-RETRO-retro` not `retro`
- `tests/test_create_retro_stories.py` references `F-RETRO-retro` not `retro`
- All existing tests pass (pytest green)
- Story files' `Feature:` lines are unchanged
- No model/provider names introduced

## Test criteria (must exist BEFORE implementation)

- `tests/test_feature_hierarchy.py` (existing) — already validates feature folders
  exist and contain feature.md. Will pass after rename because it discovers dynamically.
- `tests/test_create_retro_stories.py` (modified) — updated path assertions verify
  the new `F-RETRO-retro` folder name.
- No new test file needed — existing dynamic tests cover the rename.
