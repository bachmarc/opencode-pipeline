# Story 09-05 — Update QA-manager, developer prompts + commands + AGENTS.md template

Status: Done
Feature: doc-model-migration (F-006)

## Context / Purpose

The QA-manager prompt still references `docs/requirements.md` as primary source and
`docs/stories/*.md`. The developer prompt references `docs/design.md` as primary
reading. Several commands reference the old model (decompose, requirements, new-project,
implement). The AGENTS.md template contains old-model language (REQ-IDs, design
sections). All need updating to reference the new feature/story-primary model.

## Requirements

- QA-manager checks acceptance criteria from story files (already does), but references
  to requirements.md as "source of truth" are updated to reflect its new role as summary
- Developer prompt: reading design.md is optional context, not mandatory; story file
  is the primary source
- Commands reference features/stories instead of requirements.md/design.md as primary
- AGENTS.md template uses feature/story language instead of REQ-ID language
- All changes are consistent with the architect.md and documenter.md updates from F-005

## Developer Targets (exactly, no more / no less)

- **`agent/qa-manager.md`** — update:
  - Checklist item 1: change "Check against `docs/requirements.md` + story acceptance
    criteria" to "Check against story **acceptance criteria** (the story file is the
    primary source). `docs/requirements.md` is a derived summary for context."
  - BLOCKED_Design section: change `docs/design.md` + `docs/stories/*.md` to
    "affected feature.md + story files"
  - Keep everything else unchanged

- **`agent/developer.md`** — update:
  - Step 1: change "Read `docs/stories/<id>.md`" to reference story files in feature
    directories: "Read your story file (found via `scripts/resolve_story.py`)"
  - Step 2: change "Read `docs/design.md`" to "Optionally read `docs/design.md`
    (Documenter-generated architecture summary) for broader context. Your story file
    contains all requirements and targets you need."
  - Keep everything else unchanged

- **`command/decompose.md`** — update:
  - Change "Decompose based on `docs/requirements.md` + `docs/design.md`" to
    "Decompose into features and stories based on user requirements"
  - Change "Create `STORIES.md` + `docs/stories/`" to reference feature directories
  - Keep script references

- **`command/requirements.md`** — update:
  - Change "Create `docs/requirements.md`, `docs/design.md`" to
    "Create feature files (`docs/features/<name>/feature.md`) with vision + context,
    and story files with self-contained requirements"
  - Keep folder + git creation, interview instruction

- **`command/new-project.md`** — update:
  - Change base structure list: replace `docs/requirements.md`, `docs/design.md`,
    `STORIES.md`, `docs/stories/_template.md` with feature-based structure:
    `docs/features/_feature_template.md`, `docs/features/_story_template.md`
  - Keep all other structure items (AGENTS.md, tests/fakes, src/core, src/adapters, etc.)

- **`command/implement.md`** — update:
  - Change "developer targets from `docs/stories/<id>.md`" to reference story files
    via resolve_story.py (already partially does)
  - Change "list open stories from STORIES.md" to use pipeline_status.py or
    feature directories

- **`templates/AGENTS.md`** — update constant sections:
  - Workflow section: change "update docs (REQ-IDs, design sections, story files)" to
    "create features (vision + context) and self-contained stories"
  - Workflow section: change "Every story links traceability (`REQ-XXX` + design section)"
    to "Every story is self-contained (context, requirements, acceptance criteria, targets, tests)"
  - References section: change "docs/requirements.md — source of truth for scope (REQ-IDs)"
    to "docs/requirements.md — Documenter-generated feature overview (derived summary)"
  - References section: change "docs/design.md — source of truth for architecture"
    to "docs/design.md — Documenter-generated architecture summary (derived)"

- **`AGENTS.md`** (repo root) — update:
  - References section: same changes as templates/AGENTS.md
  - Workflow section: same changes as templates/AGENTS.md
  - Core rules: update "source of truth: `docs/requirements.md` + `docs/design.md`"
    to "source of truth: feature files + story files"

- **No other files changed.**

## Acceptance criteria (checked by qa-manager)

- qa-manager.md does not reference requirements.md as "source of truth" for checking
- developer.md references story file as primary source (not design.md)
- All 4 updated commands reference features/stories (not requirements.md as primary)
- templates/AGENTS.md Workflow section does not mention REQ-IDs as traceability anchors
- templates/AGENTS.md References section describes requirements.md as derived summary
- AGENTS.md (root) is consistent with templates/AGENTS.md changes
- All agent files have valid frontmatter (no model: key)
- No concrete model/provider names in any changed file

## Test criteria (must exist BEFORE implementation)

- `tests/test_migration.py::test_qa_prompt_no_requirements_source_of_truth` — asserts qa-manager.md does not contain "source of truth" in combination with requirements.md
- `tests/test_migration.py::test_developer_prompt_story_primary` — asserts developer.md contains language indicating story file is primary source
- `tests/test_migration.py::test_template_no_req_id_traceability` — asserts templates/AGENTS.md Workflow section does not contain `REQ-XXX` as traceability anchor pattern
- `tests/test_migration.py::test_template_references_derived` — asserts templates/AGENTS.md References section contains "derived" or "summary" for requirements.md
- `tests/test_migration.py::test_agents_md_references_derived` — asserts root AGENTS.md References section contains "derived" or "summary" for requirements.md
- `tests/test_migration.py::test_commands_no_primary_requirements` — reads decompose.md, requirements.md (command), new-project.md; asserts none instructs creating requirements.md as primary source
