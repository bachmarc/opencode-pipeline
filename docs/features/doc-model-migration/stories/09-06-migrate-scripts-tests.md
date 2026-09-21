# Story 09-06 — Update scripts + tests that reference REQ-IDs

Status: Done
Feature: doc-model-migration (F-006)

## Context / Purpose

Several scripts and test files contain REQ-ID references: `create_story.py` accepts
a `--req` parameter and fills REQ-ID placeholders, `pipeline_status.py` parses
`req:` from feature frontmatter, and test fixtures in test_check_scripts.py,
test_feature_claim.py, and test_story_mgmt.py use old-model content. These need
updating to work with the new feature/story-primary model.

## Requirements

- create_story.py no longer requires `--req` parameter (features are the reference,
  not REQ-IDs); it fills `Feature:` line instead of `Traceability:`
- pipeline_status.py no longer parses `req:` field (or handles its absence gracefully)
- Test fixtures use new-model content (Feature: instead of Traceability:, no req: field)
- All scripts remain functional with the new template/file formats
- Existing test_templates.py tests (from 08-01) continue to pass

## Developer Targets (exactly, no more / no less)

- **`scripts/create_story.py`** — update:
  - Change `--req` parameter: make optional or replace with `--feature` parameter
    that fills the `Feature:` line in the story template
  - Update template filling: replace `<REQ-XXX>` placeholder logic with
    `Feature:` line logic
  - Keep story ID generation and file creation logic

- **`scripts/pipeline_status.py`** — update:
  - Remove or make optional the `req:` field parsing from feature.md frontmatter
  - If `req:` field is absent, don't error (graceful handling)

- **`tests/test_check_scripts.py`** — update fixtures:
  - AGENTS.md template text fixtures: update to new-model language (no REQ-ID
    references in Workflow/References sections)

- **`tests/test_feature_claim.py`** — update fixtures:
  - Mock feature.md content: remove `req: [REQ-001]` or update to empty `req: []`
    or remove field entirely

- **`tests/test_story_mgmt.py`** — update fixtures:
  - Mock feature.md content: update `req:` field
  - Mock story content: use `Feature:` instead of `Traceability: REQ-999`
  - Update assertions that check for old-format content

- **No other files changed.**

## Acceptance criteria (checked by qa-manager)

- create_story.py works without `--req` parameter (or with `--feature` instead)
- create_story.py generates story files with `Feature:` line (not `Traceability:`)
- pipeline_status.py does not error on feature.md files without `req:` field
- All test fixtures use new-model content
- Full pytest suite passes (no regressions)
- No `REQ-` references remain in scripts as functional requirements (may appear in
  comments explaining migration)

## Test criteria (must exist BEFORE implementation)

- `tests/test_migration.py::test_create_story_no_req_required` — calls create_story.py without --req, asserts it succeeds (or with --feature instead)
- `tests/test_migration.py::test_create_story_generates_feature_line` — asserts created story file contains `Feature:` line
- `tests/test_migration.py::test_pipeline_status_no_req_field` — creates a feature.md without `req:` field, runs pipeline_status.py, asserts no error
- Existing tests in test_story_mgmt.py, test_feature_claim.py, test_check_scripts.py must pass after fixture updates
