# Story 11-04 — Architect Code Guard

Status: Done
Feature: pipeline-enforcement (F-007)

## Context / Purpose

The architect role must not silently write code. Today this is a prompt rule ("Architect writes
NO code"). But the LLM regularly violates this — especially for "obvious" one-liners. The
Architect Code Guard intercepts `edit` and `write` tool calls targeting code files when the
current agent is the architect.

Instead of a hard block, the guard asks the user interactively: "Kleinigkeit selbst fixen
(Housekeeping-Story) oder Pipeline starten?" This respects the reality that sometimes a
one-character typo fix doesn't warrant a full pipeline — but it must never happen silently.

If the user chooses "Housekeeping", the guard logs the change in
`.pipeline/housekeeping-log.md` with timestamp, file, and description. If the user chooses
"Pipeline", the edit is blocked and the architect must create a proper story.

## Requirements

- `tool.execute.before` on `edit` and `write` tools: if current agent is architect AND
  target file matches code patterns (`*.py`, `*.ts`, `*.js`, `*.sh`, or paths under
  `src/`, `tests/`, `plugins/guards/`):
  - Use the `question` tool or throw with a descriptive message asking the user to decide
  - Option A: "Housekeeping — log and allow" → append entry to `.pipeline/housekeeping-log.md`,
    allow the edit
  - Option B: "Pipeline — block and create story" → throw Error blocking the edit
- Guard detects agent from plugin context (`context.agent`).
- Code file patterns are configurable as a list in the guard.
- `.pipeline/housekeeping-log.md` format: `| <timestamp> | <file> | <agent> | <description> |`

## Developer Targets (exactly, no more / no less)

- Create `plugins/guards/architect-code-guard.ts`:
  - Export `architectCodeGuard(agent: string, tool: string, filePath: string, directory: string): {action: "allow" | "block", reason: string}`
  - Define code file patterns: `*.py`, `*.ts`, `*.js`, `*.sh`, `src/**`, `tests/**`, `plugins/guards/**`
  - If agent is not architect → return allow (pass through)
  - If file doesn't match code patterns → return allow
  - If both match → return block with descriptive reason asking user to decide
- Create `plugins/helpers/housekeeping-log.ts`:
  - Export `appendHousekeepingEntry(directory: string, filePath: string, agent: string, description: string): void`
  - Append markdown table row to `.pipeline/housekeeping-log.md` (create file if not exists)
- Update `plugins/pipeline-enforcement.ts`:
  - Import and register `architectCodeGuard`
  - In `tool.execute.before`: if `input.tool === "edit"` or `input.tool === "write"`,
    call `architectCodeGuard` with context.agent and file path
  - If guard returns "block" → throw Error with the reason message (includes instructions
    for user: housekeeping vs pipeline choice)
- Create `tests/test_architect_code_guard.py`:
  - Test that `plugins/guards/architect-code-guard.ts` exists
  - Test that architect-code-guard.ts contains code file patterns
  - Test that architect-code-guard.ts checks agent identity
  - Test that architect-code-guard.ts returns block for architect + code file
  - Test that `plugins/helpers/housekeeping-log.ts` exists
  - Test that pipeline-enforcement.ts imports architect-code-guard

## Acceptance criteria (checked by qa-manager)

- `plugins/guards/architect-code-guard.ts` exists and exports `architectCodeGuard`
- Guard checks agent identity AND file path pattern
- Guard returns "block" with descriptive message for architect editing code files
- Guard returns "allow" for non-architect agents or non-code files
- `plugins/helpers/housekeeping-log.ts` exists and appends to `.pipeline/housekeeping-log.md`
- Guard is registered in `pipeline-enforcement.ts`
- All tests pass

## Test criteria (must exist BEFORE implementation)

- `tests/test_architect_code_guard.py::test_architect_code_guard_file_exists` — plugins/guards/architect-code-guard.ts exists
- `tests/test_architect_code_guard.py::test_guard_has_code_patterns` — file contains code file patterns (*.py, *.ts, src/, tests/)
- `tests/test_architect_code_guard.py::test_guard_checks_agent` — file contains agent identity check
- `tests/test_architect_code_guard.py::test_guard_blocks_architect_code` — file contains block/throw logic for architect + code
- `tests/test_architect_code_guard.py::test_housekeeping_log_exists` — plugins/helpers/housekeeping-log.ts exists
- `tests/test_architect_code_guard.py::test_plugin_imports_architect_guard` — pipeline-enforcement.ts imports architect-code-guard
