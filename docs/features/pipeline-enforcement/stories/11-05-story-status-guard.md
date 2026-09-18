# Story 11-05 — Story Status Guard

Status: Planned
Feature: pipeline-enforcement (F-007)

## Context / Purpose

After a branch is merged into main, STORIES.md should be updated to reflect the new status.
Today this is a manual step that the architect frequently forgets. The Story Status Guard
detects when a `git merge` command succeeds and checks whether STORIES.md was updated in the
same session.

This guard uses `tool.execute.after` (post-merge check) rather than `tool.execute.before`
(pre-merge block). It warns rather than blocks — the merge already happened, but the architect
gets a clear reminder.

## Requirements

- `tool.execute.after` on `bash` tool: if command was `git merge <branch>` and it succeeded:
  - Extract branch name
  - Derive story ID from branch name (pattern: `feature/<story-id>-<slug>`)
  - Read `STORIES.md` and check if the story's status line contains "Done" or the merge commit
  - If not updated → emit warning: "STORIES.md not updated for <story-id> after merge.
    Please update status to Done."
- Guard is a pure function, testable without opencode runtime.
- Guard is advisory (warn), not blocking.

## Developer Targets (exactly, no more / no less)

- Create `plugins/guards/story-status-guard.ts`:
  - Export `storyStatusGuard(command: string, directory: string): string | null`
    (returns warning message or null if OK)
  - Parse branch name from `git merge <branch>` pattern
  - Extract story ID from branch name using `feature/(<story-id>)-<slug>` pattern
  - Read `STORIES.md` and check if story line contains "Done"
  - Return warning string if not updated, null if OK
- Update `plugins/pipeline-enforcement.ts`:
  - Import and register `storyStatusGuard`
  - Add `tool.execute.after` hook: if `input.tool === "bash"` and command was `git merge`,
    call `storyStatusGuard`, log any warning
- Create `tests/test_story_status_guard.py`:
  - Test that `plugins/guards/story-status-guard.ts` exists
  - Test that story-status-guard.ts extracts story ID from branch name
  - Test that story-status-guard.ts reads STORIES.md
  - Test that pipeline-enforcement.ts imports story-status-guard
  - Test that pipeline-enforcement.ts has `tool.execute.after` hook

## Acceptance criteria (checked by qa-manager)

- `plugins/guards/story-status-guard.ts` exists and exports `storyStatusGuard`
- Guard extracts story ID from branch name
- Guard reads STORIES.md for status check
- Guard returns warning (not throws) — advisory, not blocking
- Guard is registered in `pipeline-enforcement.ts` under `tool.execute.after`
- All tests pass

## Test criteria (must exist BEFORE implementation)

- `tests/test_story_status_guard.py::test_story_status_guard_file_exists` — plugins/guards/story-status-guard.ts exists
- `tests/test_story_status_guard.py::test_guard_extracts_story_id` — file contains branch-to-story-id extraction pattern
- `tests/test_story_status_guard.py::test_guard_reads_stories_md` — file contains "STORIES.md"
- `tests/test_story_status_guard.py::test_plugin_imports_story_status_guard` — pipeline-enforcement.ts imports story-status-guard
- `tests/test_story_status_guard.py::test_plugin_has_after_hook` — pipeline-enforcement.ts contains "tool.execute.after"
