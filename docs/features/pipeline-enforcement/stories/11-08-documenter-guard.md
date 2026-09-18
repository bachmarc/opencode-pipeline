# Story 11-08 — Documenter Guard

Status: Planned
Feature: pipeline-enforcement (F-007)

## Context / Purpose

The pipeline workflow requires the Documenter agent to run after QA-PASS and before merge:
QA-PASS → Documenter → Merge. In practice, the architect skips the Documenter step and merges
directly after QA-PASS. The Documenter Guard enforces this by checking whether a documenter
commit exists on the feature branch before allowing a merge.

The Documenter agent commits with message pattern `docs: reconcile *`. The guard inspects the
branch's commit history for this pattern. If no documenter commit is found after the last
non-docs commit, the merge is blocked with a clear message telling the architect to run
`/document` first.

This guard is separate from the Merge Guard (11-02) which checks QA-PASS. Both guards fire
on `git merge` commands — the merge only proceeds if both pass.

## Requirements

- `tool.execute.before` on `bash` tool: if command matches `git merge <branch>` pattern:
  - Extract branch name
  - Inspect commit log of the branch for a commit matching `docs: reconcile` pattern
  - If no documenter commit found → throw Error: "Documenter not run. Execute `/document`
    on branch <branch> before merging."
  - If documenter commit found → allow through
- Guard is a pure function: receives branch name and directory, returns void or throws.
- Guard checks commits on the feature branch only (not main).
- Guard is registered in the plugin's guard registry, runs alongside (not instead of)
  the Merge Guard.

## Developer Targets (exactly, no more / no less)

- Create `plugins/guards/documenter-guard.ts`:
  - Export `documenterGuard(command: string, directory: string, $: BunShell): Promise<void>`
  - Parse branch name from `git merge <branch>` pattern
  - Run `git log <branch> --oneline --grep="docs: reconcile"` to find documenter commits
  - If no matching commit found → throw descriptive error
  - If found → return silently
- Update `plugins/pipeline-enforcement.ts`:
  - Import and register `documenterGuard`
  - In `tool.execute.before`: if `input.tool === "bash"` and command matches `git merge`,
    call `documenterGuard` (in addition to existing `mergeGuard`)
- Create `tests/test_documenter_guard.py`:
  - Test that `plugins/guards/documenter-guard.ts` exists
  - Test that documenter-guard.ts contains `docs: reconcile` pattern
  - Test that documenter-guard.ts runs git log to check for documenter commits
  - Test that documenter-guard.ts throws on missing documenter commit
  - Test that pipeline-enforcement.ts imports documenter-guard

## Acceptance criteria (checked by qa-manager)

- `plugins/guards/documenter-guard.ts` exists and exports `documenterGuard`
- Guard checks branch commit history for `docs: reconcile` pattern
- Guard throws descriptive error when no documenter commit found
- Guard passes silently when documenter commit exists
- Guard is registered in `pipeline-enforcement.ts` alongside merge-guard
- All tests pass

## Test criteria (must exist BEFORE implementation)

- `tests/test_documenter_guard.py::test_documenter_guard_file_exists` — plugins/guards/documenter-guard.ts exists
- `tests/test_documenter_guard.py::test_guard_checks_reconcile_pattern` — file contains "docs: reconcile"
- `tests/test_documenter_guard.py::test_guard_uses_git_log` — file contains "git log" command
- `tests/test_documenter_guard.py::test_guard_throws_on_missing_documenter` — file contains throw/Error for missing documenter
- `tests/test_documenter_guard.py::test_plugin_imports_documenter_guard` — pipeline-enforcement.ts imports documenter-guard
