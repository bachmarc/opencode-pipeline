# Story 27-01 — Story Template: Tooling Gates

Status: Planned
Feature: Tooling-Gate Bootstrap (F-027)

## Codebase Snapshot

- `docs/features/_story_template.md` — current template ends at `## Test criteria`. No Tooling Gates section. Lines 1–30 (full file).
- `agents/architect.md` — "Gather requirements" section (lines 38–42) has no runtime-version interview requirement. "Decompose features & stories" section (lines 56–64) has no Tooling Gates mention.
- `agents/qa-manager.md` — Checklist section (lines 27–50). Item 2 covers tests, item 3 covers architecture. No tooling-gates check item.
- `templates/AGENTS.md` — "Workflow" constant section. No mention of lint/typecheck/format as QA gates.
- `tests/test_templates.py` — existing tests for template structure (frontmatter, sections present).
- `tests/test_architect_prompt.py` — existing tests for architect prompt content.
- `tests/test_qa_manager_prompt.py` — existing tests for QA-manager prompt content (if exists).

## Context / Purpose

QA passed VirtOffice Story 01-01 despite broken lint/typecheck/format — because none of
these were required anywhere. The root cause: the story template has no Tooling Gates
section, so Developer doesn't write them, and QA (a deterministic judge) only checks
what's in the story.

This story closes the template gap. After this story:
- Every new story has a mandatory `## Tooling Gates` section
- Architect's prompt reminds to ask for runtime version at scaffold stories
- QA-Manager's checklist explicitly covers tooling gates
- `templates/AGENTS.md` constant section mentions tooling gates as QA obligation

## Requirements

1. `docs/features/_story_template.md` gets a new mandatory section `## Tooling Gates`
   placed after `## Test criteria`, with checklist items for: tests, lint, typecheck,
   format-check, audit. Each item references "the command from `qa_config.json`".

2. `agents/architect.md` gets an explicit rule in the "Gather requirements" section:
   For any scaffold or setup story (new project, 01-xx stories, onboarding), Architect
   must ask: runtime version (e.g. Node 24, Python 3.11), package manager (npm/yarn/pnpm),
   existing tooling constraints (CI system, internal registry). These go into the story
   as an "Environment Constraints" note.

3. `agents/qa-manager.md` Checklist gets a new item 2b (after "Tests green & complete"):
   **Tooling gates green?** — QA must verify that lint, typecheck, format-check, and
   audit pass as configured in `qa_config.json`. If the story's Tooling Gates section
   is missing or any gate is not verified → FAIL.

4. `templates/AGENTS.md` constant Workflow section gets a note that lint/typecheck/
   format-check/audit are mandatory QA gates alongside tests — not optional extras.

5. `docs/features/_story_template.md` is also copied into provisioned projects by
   `provision_structure.py` — so the change propagates automatically to new projects.
   (No code change needed; `provision_structure.py` already copies the template.)

## Developer Targets (exactly, no more / no less)

- `docs/features/_story_template.md`: Add `## Tooling Gates (mandatory — QA checks ALL of these)` section after `## Test criteria`. Content:
  ```markdown
  ## Tooling Gates (mandatory — QA checks ALL of these)

  Commands come from `qa_config.json` in the project root.

  - [ ] Tests green (configured checkers in `qa_config.json`)
  - [ ] Lint clean (e.g. `eslint`, `rubocop`, `ruff`)
  - [ ] Typecheck clean (e.g. `tsc`, `mypy`) — if typed language
  - [ ] Format check clean (e.g. `prettier`, `black`) — if formatter configured
  - [ ] Audit clean (e.g. `npm-audit`, `bundler-audit`) — 0 high/critical
  ```

- `agents/architect.md`: In the "Gather requirements" bullet list, add after the existing bullets:
  ```
  - **Scaffold stories (new project, 01-xx, setup):** Before writing the story, ask:
    runtime version (Node.js, Python, Ruby, JVM), package manager (npm/yarn/pnpm/bundler),
    existing tooling constraints (CI, internal registry, proxy). Add answers as
    `## Environment Constraints` to the story — version mismatches become explicit targets.
  ```

- `agents/qa-manager.md`: In the Checklist, after item 2 ("Tests green & complete?"), insert new item:
  ```
  2b. **Tooling gates green?**
      - Story has a `## Tooling Gates` section? If missing → FAIL.
      - All configured gates verified (lint, typecheck, format, audit)?
        Unverified gate = FAIL. Gate command not found = FAIL (not skip).
  ```

- `templates/AGENTS.md`: In the constant "Workflow" section, add to the Stories item:
  ```
  Tooling gates (lint, typecheck, format-check, audit) are mandatory QA gates — same
  level as tests. Configured in `qa_config.json`. QA checks ALL of them.
  ```

- Update docstrings/module headers in every changed file.
- `tests/test_templates.py`: Add test `test_story_template_has_tooling_gates_section` — asserts `## Tooling Gates` present in `_story_template.md`.
- `tests/test_architect_prompt.py`: Add test `test_architect_prompt_has_scaffold_runtime_question` — asserts scaffold/runtime interview requirement present in `agents/architect.md`.
- `tests/test_qa_manager_prompt.py` (create if missing): Add test `test_qa_manager_has_tooling_gates_checklist_item` — asserts tooling-gates checklist item present in `agents/qa-manager.md`.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `docs/features/_story_template.md` contains a `## Tooling Gates` section with all 5 checklist items.
- `agents/architect.md` contains "scaffold" and "runtime version" and "Environment Constraints" in the requirements section.
- `agents/qa-manager.md` contains a tooling-gates checklist item (item 2b or equivalent) that requires the section to be present and all gates verified.
- `templates/AGENTS.md` mentions tooling gates as mandatory QA gates.
- All 3 new tests pass.
- No existing tests broken.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (`pytest` — this is a docs-only story, pytest checks the new tests)
- [ ] Lint clean — N/A (no Python code changed)
- [ ] Typecheck clean — N/A
- [ ] Format check clean — N/A
- [ ] Audit clean — N/A

## Test criteria (must exist BEFORE implementation)

- `tests/test_templates.py::test_story_template_has_tooling_gates_section` — reads `docs/features/_story_template.md`, asserts `## Tooling Gates` present. Protects: ensures every new story scaffolded from template has the section.
- `tests/test_architect_prompt.py::test_architect_prompt_has_scaffold_runtime_question` — reads `agents/architect.md`, asserts "scaffold" and "runtime" and "Environment Constraints" present. Protects: ensures Architect can't forget the runtime interview.
- `tests/test_qa_manager_prompt.py::test_qa_manager_has_tooling_gates_checklist_item` — reads `agents/qa-manager.md`, asserts "Tooling gates" (case-insensitive) present in checklist. Protects: ensures QA gate is not silently skippable.
