# Story 09-01 — Migrate feature.md files to new format

Status: Planned
Feature: doc-model-migration (F-006)

## Context / Purpose

5 of 6 feature.md files still use the old format: `Scope` section instead of
`Vision` + `Context`, and `req: [REQ-xxx]` in frontmatter. Only doc-model-reform
already uses the new format. These files need to be migrated so the entire repo
consistently uses the new documentation model where features carry their own
vision and context.

## Requirements

- All 5 old-format feature.md files are rewritten with Vision + Context sections
- The `req:` field in YAML frontmatter is removed (or set to empty)
- The existing Scope content is redistributed into Vision (what emerges) and
  Context (why it exists, what problem it solves)
- Story lists are preserved and updated with current status
- No information is lost — all content from Scope is captured in Vision/Context

## Developer Targets (exactly, no more / no less)

- **`docs/features/retro/feature.md`** — rewrite:
  - Remove `req: [REQ-002]` from frontmatter (set to empty or remove field)
  - Replace `## Scope` with `## Vision` + `## Context`
  - Vision: retroactive documentation of pre-pipeline changes is complete
  - Context: changes were made directly before the pipeline existed; documenting them
    ensures traceability for the project history

- **`docs/features/foundation/feature.md`** — rewrite:
  - Remove `req: [REQ-001, ...]` from frontmatter
  - Replace `## Scope` with `## Vision` + `## Context`
  - Vision: repo has AGENTS.md, docs structure, self-checks, deploy procedure, versioning
  - Context: the pipeline repo needed its own dogfooded structure

- **`docs/features/i18n/feature.md`** — rewrite:
  - Remove `req: [REQ-007, NFR-001]` from frontmatter
  - Replace `## Scope` with `## Vision` + `## Context`
  - Vision: all portable files are English, dialogue language decoupled
  - Context: international portability required English-first files

- **`docs/features/docs/feature.md`** — rewrite:
  - Remove `req: [REQ-008, REQ-014]` from frontmatter
  - Replace `## Scope` with `## Vision` + `## Context`
  - Vision: README explains the full workflow and is user-oriented
  - Context: README was inside-out, needed restructuring for new users

- **`docs/features/pipeline-evolution/feature.md`** — rewrite:
  - Remove `req: [REQ-009, ...]` from frontmatter
  - Replace `## Scope` with `## Vision` + `## Context`
  - Vision: pipeline has deterministic scripts, session recovery, multi-user support,
    documenter agent, feature hierarchy
  - Context: LLM free-hand operations needed deterministic replacements

- **No other files changed.**

## Acceptance criteria (checked by qa-manager)

- All 5 feature.md files have `## Vision` and `## Context` sections
- No feature.md file has `## Scope` section
- No feature.md file has non-empty `req:` field in frontmatter referencing REQ-IDs
- Story lists in each feature.md are preserved
- doc-model-reform/feature.md is unchanged (already new format)

## Test criteria (must exist BEFORE implementation)

- `tests/test_migration.py::test_all_features_have_vision_context` — reads all feature.md files under docs/features/*/feature.md, asserts each has `## Vision` and `## Context`
- `tests/test_migration.py::test_no_features_have_scope` — asserts no feature.md has `## Scope`
- `tests/test_migration.py::test_no_features_have_req_ids` — asserts no feature.md frontmatter has non-empty `req:` with REQ- values
