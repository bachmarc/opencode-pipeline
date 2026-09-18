# Story 09-04 — Rewrite requirements.md + design.md as Documenter-style summaries

Status: Planned
Feature: doc-model-migration (F-006)

## Context / Purpose

requirements.md and design.md are currently architect-primary documents with REQ-IDs
as anchors and 15 numbered design sections. In the new model, these become
Documenter-generated summaries: derived overviews that reference features and stories,
serving as a quick-start for the Architect.

This story rewrites both files to match the new role.

## Requirements

- requirements.md becomes a feature overview: lists all features with their vision,
  status, and story references. No REQ-IDs as primary anchors.
- design.md becomes an architecture summary: collects architecture decisions and
  patterns, references features/stories for context. No §-numbered sections tied to
  REQ-IDs.
- Both files clearly state they are derived summaries (not primary sources)
- Both files contain references back to source features/stories
- All architectural content is preserved (just restructured and referenced differently)
- The "Out of scope" and "Decisions" content is preserved

## Developer Targets (exactly, no more / no less)

- **`docs/requirements.md`** — complete rewrite as Documenter-style summary:
  - Header: clearly state this is a derived summary generated from features/stories
  - Feature overview table: Feature ID | Title | Vision (1-line) | Status | Stories
  - List all 7 features (F-RETRO through F-006)
  - Non-functional requirements section: keep NFR content but reference features
    instead of REQ-IDs
  - Out of scope section: preserve as-is
  - Remove: Problem/Goal group sections (that context now lives in features),
    individual REQ-ID definitions

- **`docs/design.md`** — complete rewrite as Documenter-style summary:
  - Header: clearly state this is a derived summary generated from features/stories
  - Architecture overview: two-clone topology, self-check architecture, deploy
    procedure — restructured as topic sections (not §-numbered, not REQ-ID-anchored)
  - Decisions table: preserve all D1-D13 decisions, reference features instead of REQ-IDs
  - Script inventory table: preserve, reference features instead of REQ-IDs
  - Each section references the source feature/story for full context
  - Remove: §-numbers as section identifiers, REQ-ID anchors in section titles

- **No other files changed.**

## Acceptance criteria (checked by qa-manager)

- requirements.md states it is a derived summary (not primary source)
- requirements.md contains a feature overview table with all 7 features
- requirements.md contains no `REQ-` definitions (no "REQ-001 Two-clone topology:" pattern)
- design.md states it is a derived summary (not primary source)
- design.md contains no `§` section numbering tied to REQ-IDs
- design.md preserves all architecture content (two-clone, self-checks, scripts, etc.)
- design.md Decisions table is preserved
- Both files contain feature/story references
- No information from the original files is lost (may be restructured)

## Test criteria (must exist BEFORE implementation)

- `tests/test_migration.py::test_requirements_is_derived_summary` — asserts requirements.md contains "derived" or "summary" or "generated from features" language
- `tests/test_migration.py::test_requirements_has_feature_table` — asserts requirements.md contains a table with feature IDs (F-RETRO, F-001, etc.)
- `tests/test_migration.py::test_requirements_no_req_definitions` — asserts requirements.md does not contain the pattern `REQ-\d+\s+\w` (REQ-ID followed by title, the old definition format)
- `tests/test_migration.py::test_design_is_derived_summary` — asserts design.md contains "derived" or "summary" or "generated from features" language
- `tests/test_migration.py::test_design_no_numbered_req_sections` — asserts design.md does not contain `## \d+\. .* \(REQ-` pattern (old §-numbered sections with REQ-IDs)
- `tests/test_migration.py::test_design_has_decisions_table` — asserts design.md still contains a Decisions table (with `| D` rows)
