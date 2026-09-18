# Story 11-07 — Session Recovery Guard

Status: Planned
Feature: pipeline-enforcement (F-007)

## Context / Purpose

The architect prompt says "Before any work: Run `scripts/session_recovery.py` to scan the full
state." In practice, the LLM skips this regularly — especially when the user jumps straight
into a request. The Session Recovery Guard enforces this at plugin level.

On the first tool call of a session, the plugin runs `session_recovery.py --check` and
inspects the result. If recovery items exist (open intents, dirty worktrees, merge conflicts),
the guard blocks all further work until the architect has addressed them. This prevents the
common failure mode where the architect starts fresh work while a previous session's branches,
worktrees, or intents are still dangling.

The guard uses a session-local flag to track whether recovery has been performed — it only
fires once per session (on the first tool call), not on every call.

## Requirements

- On the first `tool.execute.before` call in a session (any tool, any agent):
  - Run `python3 scripts/session_recovery.py --check` via subprocess
  - If exit code is 1 (recovery items exist): throw Error with the recovery summary,
    blocking the tool call. Message includes: "Session recovery required. Run
    `scripts/session_recovery.py` and address open items before continuing."
  - If exit code is 0 (clean): set session-local flag `recoveryDone = true`, allow through
  - On subsequent calls: skip check (flag is set)
- Guard only fires for the `architect` agent (build agent). Developer and QA subagents
  don't need recovery — they work in isolated worktrees.
- If `session_recovery.py` is not found (e.g., non-pipeline project): skip silently.
  The plugin must be safe to load in any project.

## Developer Targets (exactly, no more / no less)

- Create `plugins/guards/session-recovery-guard.ts`:
  - Export `sessionRecoveryGuard(agent: string, directory: string, $: BunShell): Promise<void>`
  - Run `python3 scripts/session_recovery.py --check` using Bun shell
  - Parse exit code: 0 = clean, 1 = recovery needed
  - Capture stderr (human-readable summary) for the error message
  - Throw descriptive error if recovery needed
  - Return silently if clean or if script not found
- Create `plugins/helpers/session-state.ts`:
  - Export `SessionState` class with `recoveryDone: boolean` flag
  - Provides `markRecoveryDone()` and `isRecoveryDone()` methods
  - Single instance per plugin initialization (session-scoped)
- Update `plugins/pipeline-enforcement.ts`:
  - Import `sessionRecoveryGuard` and `SessionState`
  - Create `SessionState` instance in plugin init
  - In `tool.execute.before`: if `!sessionState.isRecoveryDone()` and agent is architect,
    call `sessionRecoveryGuard`. On success, call `sessionState.markRecoveryDone()`.
- Create `tests/test_session_recovery_guard.py`:
  - Test that `plugins/guards/session-recovery-guard.ts` exists
  - Test that session-recovery-guard.ts references `session_recovery.py`
  - Test that session-recovery-guard.ts checks exit code
  - Test that session-recovery-guard.ts throws on recovery needed
  - Test that `plugins/helpers/session-state.ts` exists
  - Test that pipeline-enforcement.ts imports session-recovery-guard

## Acceptance criteria (checked by qa-manager)

- `plugins/guards/session-recovery-guard.ts` exists and exports `sessionRecoveryGuard`
- Guard runs `session_recovery.py --check` via subprocess
- Guard throws descriptive error when recovery items exist (exit code 1)
- Guard passes silently when clean (exit code 0) or script not found
- `plugins/helpers/session-state.ts` provides session-scoped flag
- Guard only fires once per session (first tool call)
- Guard only fires for architect agent
- Guard is registered in `pipeline-enforcement.ts`
- All tests pass

## Test criteria (must exist BEFORE implementation)

- `tests/test_session_recovery_guard.py::test_session_recovery_guard_file_exists` — plugins/guards/session-recovery-guard.ts exists
- `tests/test_session_recovery_guard.py::test_guard_references_recovery_script` — file contains "session_recovery.py"
- `tests/test_session_recovery_guard.py::test_guard_checks_exit_code` — file contains exit code / returncode check
- `tests/test_session_recovery_guard.py::test_guard_throws_on_recovery_needed` — file contains throw/Error for recovery
- `tests/test_session_recovery_guard.py::test_session_state_exists` — plugins/helpers/session-state.ts exists
- `tests/test_session_recovery_guard.py::test_plugin_imports_session_recovery_guard` — pipeline-enforcement.ts imports session-recovery-guard
