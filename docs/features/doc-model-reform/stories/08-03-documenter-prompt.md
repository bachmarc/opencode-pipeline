# Story 08-03 — Documenter prompt: generate summaries + consistency checks

Status: Planned
Feature: doc-model-reform (F-005)

## Context / Purpose

The Documenter currently only reconciles documentation against code changes (diffs).
With the new documentation model, the Documenter gets an expanded role: it generates
and maintains `requirements.md` and `design.md` as **derived summaries** from
features and stories.

These summaries serve as a quick-start for the Architect — instead of reading every
feature and story file, the Architect reads the Documenter-generated summary to get
an overview of existing features, their status, architecture decisions, and what has
been built.

The Documenter also checks consistency: are the summaries in sync with what the
features/stories actually say? Are there orphaned references or stale information?

## Requirements

- The Documenter prompt must instruct generating/updating `docs/requirements.md` as a
  feature overview with story references (not as a primary requirements source)
- The Documenter prompt must instruct generating/updating `docs/design.md` as an
  architecture summary derived from features/stories
- The Documenter prompt must instruct consistency checking: summaries ↔ features/stories ↔ code
- The Documenter prompt must explain that these summaries serve as Architect quick-start
- The existing reconciliation duties (README, docstrings, stale comments) remain unchanged
- The "Boundary" section must clarify: Documenter generates summaries FROM features/stories,
  does not invent requirements or architecture

## Developer Targets (exactly, no more / no less)

- **`agent/documenter.md`** — extend with new responsibilities:

  1. **"Your Role" section** — expand:
     - Keep: "reconcile documentation against actual code state"
     - Add: "Generate and maintain derived summary documents (`docs/requirements.md`,
       `docs/design.md`) from feature and story files. These summaries serve as a
       quick-start for the Architect in the next session."

  2. **"Your Assignment" section** — add new step between current steps 2 and 3:
     - "**Generate/update summary documents:**
       - `docs/requirements.md`: Feature overview — list all features with their vision,
         status, and story references. This is NOT a primary requirements source; it is
         derived from `docs/features/*/feature.md`.
       - `docs/design.md`: Architecture summary — collect architecture decisions and
         patterns from feature contexts and story requirements. This is NOT a primary
         design source; it is derived from features/stories.
       - Both documents must contain clear references back to the source features/stories
         (e.g., 'See feature: doc-model-reform, story: 08-01-templates-reform')."

  3. **Add new section "## Consistency Checks":**
     - "After updating summaries, verify consistency:
       - Every feature listed in `docs/requirements.md` exists as a feature directory
       - Every story referenced exists as a story file
       - Architecture decisions in `docs/design.md` are traceable to feature/story files
       - No orphaned references (features/stories mentioned in summaries but deleted)
       - No stale status (summary says 'done' but feature says 'in-progress')
       - Report inconsistencies in your summary output"

  4. **"Boundary" section** — add clarification:
     - "**Do not invent requirements or architecture** — summaries are derived FROM
       features/stories. If a feature/story is missing context, flag it as incomplete
       rather than inventing content."

- **No other files changed.** Only `agent/documenter.md` is modified.

## Acceptance criteria (checked by qa-manager)

- `agent/documenter.md` instructs generating `docs/requirements.md` as derived feature overview
- `agent/documenter.md` instructs generating `docs/design.md` as derived architecture summary
- `agent/documenter.md` contains a "Consistency Checks" section (or equivalent)
- `agent/documenter.md` explains summaries serve as Architect quick-start
- `agent/documenter.md` clarifies summaries are derived (not primary sources)
- `agent/documenter.md` still contains existing reconciliation duties (README, docstrings, stale comments)
- `agent/documenter.md` boundary section includes "do not invent requirements or architecture"
- `agent/documenter.md` has valid frontmatter (no `model:` key, required fields present)
- No concrete model/provider names in the file

## Test criteria (must exist BEFORE implementation)

- `tests/test_documenter_prompt.py::test_instructs_generate_requirements_summary` — asserts documenter.md contains instruction to generate/update `docs/requirements.md` as derived summary
- `tests/test_documenter_prompt.py::test_instructs_generate_design_summary` — asserts documenter.md contains instruction to generate/update `docs/design.md` as derived summary
- `tests/test_documenter_prompt.py::test_has_consistency_checks` — asserts documenter.md contains consistency check instructions (orphaned references, stale status)
- `tests/test_documenter_prompt.py::test_summaries_as_architect_quickstart` — asserts documenter.md mentions summaries serving as Architect quick-start (or equivalent phrasing)
- `tests/test_documenter_prompt.py::test_summaries_are_derived` — asserts documenter.md contains "derived" or equivalent language clarifying summaries are not primary sources
- `tests/test_documenter_prompt.py::test_existing_duties_preserved` — asserts documenter.md still mentions README, docstrings, stale comments reconciliation
- `tests/test_documenter_prompt.py::test_boundary_no_invent` — asserts boundary section contains "do not invent" for requirements/architecture
- `tests/test_documenter_prompt.py::test_valid_frontmatter` — asserts valid YAML frontmatter without `model:` key
