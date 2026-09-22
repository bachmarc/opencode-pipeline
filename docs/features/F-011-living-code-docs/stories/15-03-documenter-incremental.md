# Story 15-03 — Documenter Incremental Update Mode

Status: Planned
Feature: living-code-docs (F-011)

## Context / Purpose

The Documenter agent currently receives a git diff and must figure out what documentation
to update by scanning the entire README/AGENTS.md against the diff. This unbounded scope
is why documentation drifted and was eventually deleted (F-010).

With the watermark infrastructure from story 15-02 in place, the Documenter can now work
incrementally: read the watermark, identify pending stories, read each story's Developer
Targets and the affected files' docstrings, and make targeted updates to the relevant
sections of README.md and AGENTS.md. After updating, it bumps the watermark.

This story updates the Documenter prompt to use the watermark-based incremental workflow
and adds the watermark bump to the Documenter's commit routine.

## Requirements

1. The Documenter prompt must describe the incremental workflow: read watermark → identify
   pending stories → read story targets + code docstrings → update affected sections →
   bump watermark.
2. The Documenter must bump the `synced_through` watermark after updating documentation.
3. The Documenter must still fall back to full reconciliation if the watermark is missing
   or unparseable (backward compatibility).
4. A test must verify the Documenter prompt contains watermark-related instructions.

## Developer Targets (exactly, no more / no less)

- `agent/documenter.md`: Rewrite "Your Assignment" section to describe the incremental
  workflow:
  1. Run `scripts/check_watermark.py` to find pending stories
  2. For each pending story: read the story file, identify changed files from Developer
     Targets, read those files' docstrings/headers
  3. Update README.md sections affected by the changes
  4. Update AGENTS.md sections affected by the changes
  5. Bump `synced_through` in both files to the latest incorporated story
  6. Commit with `docs: reconcile <story-ids>`
  Keep the existing "Boundary: What You Do NOT Do" and "Rules" sections. Add a fallback
  note: if watermark is missing, fall back to diff-based reconciliation (current behavior).

- `tests/test_documenter_prompt.py`: New test file with:
  - `test_documenter_has_watermark_workflow` — asserts agent/documenter.md contains
    "watermark" and "check_watermark" and "synced_through"
  - `test_documenter_has_incremental_steps` — asserts the prompt contains "pending
    stories" and "bump" in the assignment section
  - `test_documenter_has_fallback` — asserts the prompt mentions fallback behavior
    when watermark is missing

## Acceptance criteria (checked by qa-manager)

- Documenter prompt describes watermark-based incremental workflow
- Documenter prompt includes fallback for missing watermark
- Documenter prompt still contains all existing boundary rules (no removals)
- All new tests pass, all existing tests remain green
- No model/provider names introduced in any changed file

## Test criteria (must exist BEFORE implementation)

- `tests/test_documenter_prompt.py::test_documenter_has_watermark_workflow` — asserts
  "watermark" and "check_watermark" appear in agent/documenter.md
- `tests/test_documenter_prompt.py::test_documenter_has_incremental_steps` — asserts
  "pending stories" and "bump" appear in the assignment section
- `tests/test_documenter_prompt.py::test_documenter_has_fallback` — asserts "fallback"
  or "missing" appears in context of watermark handling
