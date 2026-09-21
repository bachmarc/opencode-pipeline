# Story 09-02 — Migrate story files to new 5-section format

Status: Done
Feature: doc-model-migration (F-006)

## Context / Purpose

22 story files still use the old format: `Traceability: REQ-xxx → Design §n` line,
and the old section structure (Definition, Development goal). The new model requires
self-contained stories with 5 sections (Context/Purpose, Requirements, Acceptance
criteria, Developer Targets, Test criteria) and a `Feature:` reference instead of
`Traceability:`.

These are all completed/retro stories — the migration preserves their content while
reformatting to the new structure.

## Requirements

- All 22 old-format story files are rewritten with the new 5-section structure
- `Traceability: REQ-xxx → Design §n` is replaced by `Feature: <name> (<id>)`
- Old `Definition` + `Development goal` content is redistributed into
  `Context / Purpose` + `Requirements`
- Developer Targets, Acceptance criteria, Test criteria are preserved as-is
- No information is lost

## Developer Targets (exactly, no more / no less)

- **All 22 story files** listed below — for each:
  - Replace `Traceability: ...` line with `Feature: <feature-name> (<feature-id>)`
    (derive from the feature directory the story lives in)
  - Replace `## Definition` with `## Context / Purpose` (keep content, rephrase if
    needed to answer "why does this story exist?")
  - Replace `## Development goal` with `## Requirements` (keep content, rephrase if
    needed to answer "what must be true when done?")
  - Keep `## Developer Targets`, `## Acceptance criteria`, `## Test criteria` as-is
  - If a story lacks Acceptance criteria or Test criteria sections, add them with
    the existing content or mark as `(retroactive — tests were added post-implementation)`

  Files to migrate:
  - `docs/features/foundation/stories/01-03-framework-checks.md`
  - `docs/features/foundation/stories/01-04-deploy-procedure.md`
  - `docs/features/foundation/stories/01-05-version.md`
  - `docs/features/i18n/stories/04-01-translate-agents.md`
  - `docs/features/i18n/stories/04-02-translate-commands.md`
  - `docs/features/i18n/stories/04-03-translate-template.md`
  - `docs/features/i18n/stories/04-04-translate-repo-docs.md`
  - `docs/features/pipeline-evolution/stories/06-01-feature-hierarchy.md`
  - `docs/features/pipeline-evolution/stories/06-02-pipeline-dir-intent.md`
  - `docs/features/pipeline-evolution/stories/06-03-release-branch.md`
  - `docs/features/pipeline-evolution/stories/06-04-worktree-setup.md`
  - `docs/features/pipeline-evolution/stories/06-05-pipeline-status.md`
  - `docs/features/pipeline-evolution/stories/06-06-story-management.md`
  - `docs/features/pipeline-evolution/stories/06-07-scaffold-project.md`
  - `docs/features/pipeline-evolution/stories/06-08-session-recovery.md`
  - `docs/features/pipeline-evolution/stories/06-09-feature-claim.md`
  - `docs/features/pipeline-evolution/stories/06-10-documenter-agent.md`
  - `docs/features/pipeline-evolution/stories/06-11-qa-scripts.md`
  - `docs/features/pipeline-evolution/stories/06-12-prompt-updates.md`
  - `docs/features/pipeline-evolution/stories/06-13-check-scripts.md`
  - `docs/features/pipeline-evolution/stories/06-14-orchestration-rules.md`
  - `docs/features/docs/stories/07-01-readme-restructure.md`

- **No other files changed.**

## Acceptance criteria (checked by qa-manager)

- All 22 story files have `Feature:` line (not `Traceability:`)
- All 22 story files have `## Context / Purpose` section (not `## Definition`)
- All 22 story files have `## Requirements` section (not `## Development goal`)
- No story file contains `REQ-` or `Design §` as traceability reference
- Developer Targets content is preserved in each file
- 3 stories from phase 08 are unchanged (already new format)

## Test criteria (must exist BEFORE implementation)

- `tests/test_migration.py::test_all_stories_have_feature_reference` — reads all story files under docs/features/*/stories/*.md (excluding templates), asserts each has `Feature:` line
- `tests/test_migration.py::test_no_stories_have_traceability` — asserts no story file has `Traceability:` line
- `tests/test_migration.py::test_all_stories_have_context_section` — asserts all story files have `## Context / Purpose`
- `tests/test_migration.py::test_all_stories_have_requirements_section` — asserts all story files have `## Requirements`
- `tests/test_migration.py::test_no_stories_have_old_sections` — asserts no story file has `## Definition` or `## Development goal` as section headers
