# Story 08-01 — Templates reform (self-contained stories + enriched features)

Status: Done
Feature: doc-model-reform (F-005)

## Context / Purpose

Stories are currently thin wrappers around developer targets, with their "why" living
in requirements.md (referenced via REQ-IDs). This means a story is not self-contained —
you must read requirements.md to understand the purpose. Features are just folders with
a minimal feature.md.

This story changes both templates so that:
- Stories become self-contained documents (purpose + requirements + acceptance criteria +
  developer targets + tests — all in one file)
- Features carry vision and context (what all stories together create, why it matters)

## Requirements

- The story template must have 5 sections: Context/Purpose, Requirements, Acceptance
  Criteria, Developer Targets, Test Criteria
- The story template must NOT reference REQ-IDs or Design §-numbers (those belong in
  architect overview docs, not in stories)
- The feature template must have: Vision (what emerges when all stories are done),
  Context (why this feature exists, what problem it solves), Stories (list with status)
- Both templates must be usable by cheap models (clear structure, no ambiguity)
- The old `Traceability: <REQ-XXX> → Design §<n>` line is replaced by
  `Feature: <feature-name> (<feature-id>)`

## Developer Targets (exactly, no more / no less)

- **`docs/features/_story_template.md`** — rewrite with new 5-section structure:
  ```
  # Story <ID> — <Title>
  Status: Planned | In Progress | Done
  Feature: <feature-name> (<feature-id>)

  ## Context / Purpose
  <Why does this story exist? What problem does it solve? Self-contained — no external references needed>

  ## Requirements
  <What must be true when this story is done? Functional requirements in the story's own words>

  ## Developer Targets (exactly, no more / no less)
  <Concrete changes — file by file>

  ## Acceptance criteria (checked by qa-manager)
  <Deterministically verifiable criteria>

  ## Test criteria (must exist BEFORE implementation)
  <Tests written first — file, test name, expected behavior>
  ```

- **`docs/stories/_template.md`** — same content as above (keep both locations in sync
  for backward compatibility until migration)

- **`docs/features/_feature_template.md`** — new file, feature template:
  ```
  ---
  id: F-<NNN>
  title: <Feature Title>
  status: planned | in-progress | done
  owner: ""
  ---

  ## Vision
  <What emerges when ALL stories of this feature are done? The big picture.>

  ## Context
  <Why does this feature exist? What problem does it solve? Who benefits?>

  ## Stories
  - <id>-<slug> (<status>)
  ```

## Acceptance criteria (checked by qa-manager)

- `docs/features/_story_template.md` exists with exactly 5 sections: Context/Purpose, Requirements, Developer Targets, Acceptance criteria, Test criteria
- `docs/stories/_template.md` has identical content to `docs/features/_story_template.md`
- `docs/features/_feature_template.md` exists with Vision, Context, Stories sections
- Story template contains `Feature:` line instead of `Traceability: <REQ-XXX>`
- Story template does NOT contain `REQ-` or `Design §` references
- Feature template contains YAML frontmatter with id, title, status, owner fields
- Feature template contains `## Vision` and `## Context` sections

## Test criteria (must exist BEFORE implementation)

- `tests/test_templates.py::test_story_template_has_five_sections` — reads `docs/features/_story_template.md`, asserts presence of all 5 section headings
- `tests/test_templates.py::test_story_template_no_req_ids` — asserts story template does not contain `REQ-` or `Design §`
- `tests/test_templates.py::test_story_template_has_feature_reference` — asserts story template contains `Feature:` line
- `tests/test_templates.py::test_feature_template_has_vision_context` — reads `docs/features/_feature_template.md`, asserts `## Vision` and `## Context` sections exist
- `tests/test_templates.py::test_feature_template_has_frontmatter` — asserts feature template has YAML frontmatter with id, title, status, owner
- `tests/test_templates.py::test_story_templates_in_sync` — asserts `docs/stories/_template.md` and `docs/features/_story_template.md` have identical content
