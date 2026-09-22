# Story 16-01 — Clarification Markers in Story Template + Workflow

Status: Planned
Feature: Clarification Markers (F-012)

## Context / Purpose

When the architect decomposes features into stories, ambiguous points may be silently resolved
with plausible-but-wrong assumptions. There is no formal mechanism in the story template or
workflow that forces the architect to flag uncertainty rather than guess, or that prevents
stories with unresolved ambiguities from reaching the developer.

This story adds `[NEEDS CLARIFICATION: ...]` markers as a first-class concept: the story
template instructs the architect to use them, the workflow ensures the user resolves them at
the review checkpoint, and QA verifies none survive into implementation.

## Requirements

1. The story template (`docs/features/_story_template.md`) must contain guidance instructing
   the architect to mark ambiguous or underspecified points with `[NEEDS CLARIFICATION: <specific question>]`
   instead of guessing.
2. The story template's acceptance criteria section must include a standing criterion:
   "No `[NEEDS CLARIFICATION]` markers remain in this story."
3. The architect prompt (`agent/architect.md`) must reference the marker convention in the
   story-creation rules: when writing stories, mark anything not explicitly decided by the
   user with `[NEEDS CLARIFICATION: ...]` — never silently assume.
4. The QA-manager prompt (`agent/qa-manager.md`) must include a check: if any
   `[NEEDS CLARIFICATION]` marker remains in the story file at QA time, verdict is FAIL
   (ambiguity not resolved before implementation).
5. No new scripts, plugins, or commands are required — this is purely a template + prompt change.

## Developer Targets (exactly, no more / no less)

- **`docs/features/_story_template.md`**: Add a guidance comment in the Requirements section
  instructing the use of `[NEEDS CLARIFICATION: <question>]` for anything ambiguous.
  Add a standing acceptance criterion: "No `[NEEDS CLARIFICATION]` markers remain in this story."
  Update docstrings and module headers in every file you change — code documentation is the source of truth.

- **`agent/architect.md`**: In the "Decompose features & stories" section (task 3), add a rule:
  "When writing stories, mark anything not explicitly decided by the user with
  `[NEEDS CLARIFICATION: <specific question>]` — never silently assume. The user resolves these
  at the review checkpoint before dev starts."
  Update docstrings and module headers in every file you change — code documentation is the source of truth.

- **`agent/qa-manager.md`**: In the Checklist section, add to item 1 (Requirements met?):
  "If any `[NEEDS CLARIFICATION]` marker remains in the story file → FAIL (ambiguity not resolved
  before implementation)."
  Update docstrings and module headers in every file you change — code documentation is the source of truth.

## Acceptance criteria (checked by qa-manager)

- `_story_template.md` contains the text `[NEEDS CLARIFICATION` as guidance for the architect.
- `_story_template.md` acceptance criteria section contains a standing "No `[NEEDS CLARIFICATION]` markers remain" criterion.
- `agent/architect.md` contains the marker convention in the story-decomposition rules.
- `agent/qa-manager.md` checklist item 1 includes the `[NEEDS CLARIFICATION]` → FAIL rule.
- No other files are changed.
- No `[NEEDS CLARIFICATION]` markers remain in this story.

## Test criteria (must exist BEFORE implementation)

- `tests/test_framework.py`: Add test `test_story_template_has_clarification_guidance` —
  reads `docs/features/_story_template.md`, asserts it contains the string `[NEEDS CLARIFICATION`.
- `tests/test_framework.py`: Add test `test_architect_prompt_has_clarification_rule` —
  reads `agent/architect.md`, asserts it contains `NEEDS CLARIFICATION`.
- `tests/test_framework.py`: Add test `test_qa_prompt_has_clarification_check` —
  reads `agent/qa-manager.md`, asserts it contains `NEEDS CLARIFICATION`.
