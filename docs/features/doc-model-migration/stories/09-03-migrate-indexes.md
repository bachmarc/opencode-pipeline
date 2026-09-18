# Story 09-03 — Migrate STORIES.md + FEATURES.md to feature-references

Status: Planned
Feature: doc-model-migration (F-006)

## Context / Purpose

STORIES.md and FEATURES.md still use REQ-IDs in their Traceability columns. With the
new model, these index files should reference features (not REQ-IDs) as their
traceability anchor. FEATURES.md also has an outdated directory structure description
that mentions `traceability (REQ-ID)`.

## Requirements

- STORIES.md Traceability column uses feature references (e.g., `F-001 foundation`)
  instead of REQ-IDs for all entries
- FEATURES.md Traceability column is replaced by a feature-reference or removed
  (features ARE the top-level unit now, they don't trace to REQ-IDs)
- FEATURES.md directory structure description is updated to reflect new model
  (no `traceability (REQ-ID)` mention)
- FEATURES.md includes the doc-model-reform (F-005) and doc-model-migration (F-006) features
- All existing information (story IDs, titles, status, commit hashes) is preserved

## Developer Targets (exactly, no more / no less)

- **`STORIES.md`** — update Traceability column:
  - Replace all `REQ-xxx → Design §n` references with feature references
    (e.g., `REQ-002` → `F-RETRO retro`, `REQ-003, REQ-004 → Design §3` → `F-001 foundation`)
  - Keep all other columns (Story, Title, Status) unchanged
  - Phase comments: remove REQ-ID mentions, use feature names instead

- **`FEATURES.md`** — update:
  - Remove `Traceability` column from table (features don't trace to REQ-IDs anymore)
  - Add F-005 (doc-model-reform, done) and F-006 (doc-model-migration, in-progress)
  - Update F-004 status to `done` (all 06-xx stories are done)
  - Update directory structure description: remove `traceability (REQ-ID)` mention,
    describe new model (Vision + Context)
  - Update the `feature.md` field description to mention Vision/Context instead of
    `scope, status, traceability (REQ-ID), claim info`

- **No other files changed.**

## Acceptance criteria (checked by qa-manager)

- STORIES.md contains no `REQ-` references in Traceability column
- STORIES.md contains no `Design §` references in Traceability column
- FEATURES.md contains no `Traceability` column header
- FEATURES.md contains no `REQ-` references in table rows
- FEATURES.md includes F-005 and F-006 entries
- FEATURES.md directory structure description does not mention `REQ-ID`
- All story IDs, titles, and status values are preserved in STORIES.md

## Test criteria (must exist BEFORE implementation)

- `tests/test_migration.py::test_stories_index_no_req_ids` — reads STORIES.md, asserts no table row contains `REQ-` in Traceability column
- `tests/test_migration.py::test_stories_index_no_design_refs` — asserts no table row contains `Design §`
- `tests/test_migration.py::test_features_index_no_traceability_column` — reads FEATURES.md, asserts table header does not contain `Traceability`
- `tests/test_migration.py::test_features_index_no_req_ids` — asserts FEATURES.md table rows contain no `REQ-` references
- `tests/test_migration.py::test_features_index_has_new_features` — asserts FEATURES.md contains F-005 and F-006
