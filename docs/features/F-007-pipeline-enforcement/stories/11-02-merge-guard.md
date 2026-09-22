# Story 11-02 — Merge Guard

Status: Done
Feature: pipeline-enforcement (F-007)

## Context / Purpose

The most critical process violation: merging a feature branch into main without QA-PASS.
Today this is a prompt rule ("Architect may execute git merge on main ONLY if QA-Manager has
given explicit PASS"). The Merge Guard makes this a hard gate.

When any agent runs `git merge <branch>` via the bash tool, the plugin intercepts the call,
checks `.pipeline/qa-status/<branch-name>.json` for a PASS verdict, and blocks the merge if
no PASS exists. The existing `scripts/merge_if_passed.py` already implements this logic in
Python — the plugin enforces it at the tool-call level so even direct `git merge` commands
are caught.

## Requirements

- `tool.execute.before` on `bash` tool: if command matches `git merge *` pattern:
  - Extract branch name from command
  - Check `.pipeline/qa-status/` for a file matching the branch with `"verdict": "PASS"`
  - If no PASS found → throw Error with clear message ("Merge blocked: no QA-PASS for <branch>")
  - If PASS found → allow the command through
- Guard is a pure function that receives the command string and project directory, returns
  void or throws. Testable without opencode runtime.
- Guard is registered in the plugin's guard registry.

## Developer Targets (exactly, no more / no less)

- Create `plugins/guards/merge-guard.ts`:
  - Export `mergeGuard(command: string, directory: string): void`
  - Parse branch name from `git merge <branch>` pattern
  - Read `.pipeline/qa-status/` directory for matching PASS file
  - Throw descriptive error if no PASS found
- Update `plugins/pipeline-enforcement.ts`:
  - Import and register `mergeGuard` in the guard registry
  - In `tool.execute.before`: if `input.tool === "bash"` and command matches `git merge`,
    call `mergeGuard`
- Create `tests/test_merge_guard.py`:
  - Test that `plugins/guards/merge-guard.ts` exists
  - Test that merge-guard.ts contains branch extraction logic
  - Test that merge-guard.ts reads from `.pipeline/qa-status/`
  - Test that merge-guard.ts throws on missing PASS
  - Test that pipeline-enforcement.ts imports merge-guard

## Acceptance criteria (checked by qa-manager)

- `plugins/guards/merge-guard.ts` exists and exports `mergeGuard`
- Guard checks `.pipeline/qa-status/` for PASS verdict
- Guard throws descriptive error when no PASS exists
- Guard is registered in `pipeline-enforcement.ts`
- All tests pass

## Test criteria (must exist BEFORE implementation)

- `tests/test_merge_guard.py::test_merge_guard_file_exists` — plugins/guards/merge-guard.ts exists
- `tests/test_merge_guard.py::test_merge_guard_reads_qa_status` — file contains ".pipeline/qa-status"
- `tests/test_merge_guard.py::test_merge_guard_throws_on_no_pass` — file contains throw/Error pattern for missing PASS
- `tests/test_merge_guard.py::test_plugin_imports_merge_guard` — pipeline-enforcement.ts imports merge-guard
