# Story 11-03 — Dev-Start Guard

Status: Done
Feature: pipeline-enforcement (F-007)

## Context / Purpose

The pipeline requires that no developer or QA-manager is spawned without an approved story
and explicit user-go. Today `permission.task` provides a UI gate (user must click approve),
but it doesn't verify that a story actually exists or is in the right state. The Dev-Start
Guard adds a semantic check: before a `task` tool call spawns a developer or qa-manager,
the plugin verifies that the prompt references a known story from STORIES.md that is in
an appropriate state (Planned or In Progress, not already Done).

## Requirements

- `tool.execute.before` on `task` tool: if `output.args.subagent_type` is `developer` or
  `qa-manager`:
  - Scan `output.args.prompt` for story ID patterns (e.g., `11-01`, `06-14`)
  - Look up the story in `STORIES.md`
  - If no story ID found in prompt → warn (log warning, don't block — the user-go via
    permission.task is the hard gate)
  - If story found but status is "Done" → warn ("Story already done")
  - If story not found in STORIES.md → warn ("Unknown story ID")
- Guard is a pure function, testable without opencode runtime.
- This guard is advisory (warn), not blocking — `permission.task` remains the hard gate.

## Developer Targets (exactly, no more / no less)

- Create `plugins/guards/dev-start-guard.ts`:
  - Export `devStartGuard(subagentType: string, prompt: string, directory: string): string[]`
    (returns array of warning messages, empty if all OK)
  - Parse story IDs from prompt using regex pattern `\b(\d{2}-\d{2})\b`
  - Read `STORIES.md` and check story status
  - Return warnings for: no story ID, unknown story, story already Done
- Update `plugins/pipeline-enforcement.ts`:
  - Import and register `devStartGuard`
  - In `tool.execute.before`: if `input.tool === "task"` and subagent is developer/qa-manager,
    call `devStartGuard`, log any warnings
- Create `tests/test_dev_start_guard.py`:
  - Test that `plugins/guards/dev-start-guard.ts` exists
  - Test that dev-start-guard.ts contains story ID regex
  - Test that dev-start-guard.ts reads STORIES.md
  - Test that pipeline-enforcement.ts imports dev-start-guard

## Acceptance criteria (checked by qa-manager)

- `plugins/guards/dev-start-guard.ts` exists and exports `devStartGuard`
- Guard parses story IDs from prompt text
- Guard reads STORIES.md for status verification
- Guard returns warnings (not throws) — advisory, not blocking
- Guard is registered in `pipeline-enforcement.ts`
- All tests pass

## Test criteria (must exist BEFORE implementation)

- `tests/test_dev_start_guard.py::test_dev_start_guard_file_exists` — plugins/guards/dev-start-guard.ts exists
- `tests/test_dev_start_guard.py::test_dev_start_guard_has_story_regex` — file contains story ID regex pattern
- `tests/test_dev_start_guard.py::test_dev_start_guard_reads_stories` — file contains "STORIES.md"
- `tests/test_dev_start_guard.py::test_plugin_imports_dev_start_guard` — pipeline-enforcement.ts imports dev-start-guard
