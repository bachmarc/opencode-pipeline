# Story 06-02 — .pipeline directory and intent tracking

Status: Planned
Feature: pipeline-evolution (F-004)

## Context / Purpose

Create the `.pipeline/` directory structure for mutable pipeline state (intent tracking,
QA state). This is the foundation for session recovery and QA routing.

## Requirements

After this story, `.pipeline/` exists with `intent.json` schema and `qa-state/` directory.
A Python module `scripts/intent.py` provides deterministic read/write of intents.

## Developer Targets (exactly, no more / no less)

- Create `.pipeline/` directory at repo root
- Create `.pipeline/intent.json` with initial empty state `{"intents": []}`
- Create `.pipeline/qa-state/` directory (empty, with `.gitkeep`)
- Create `scripts/intent.py` — deterministic intent management:
  - `intent.py start <story-id> <agent> <step> [--worktree <path>] [--branch <name>]`
    → appends intent entry with `done: false`, timestamp
  - `intent.py done <story-id>` → marks latest open intent for story as `done: true`
  - `intent.py show` → outputs all intents as JSON (open and closed)
  - `intent.py open` → outputs only open (not-done) intents as JSON
  - Exit code 0 on success, 1 on error (story not found, no open intent)
- Add `.pipeline/` to git tracking (intent.json and qa-state/ are shared state)
- Add `.pipeline/config.json` to `.gitignore` (local-only config)

## Acceptance criteria (checked by qa-manager)

- `.pipeline/intent.json` exists and is valid JSON
- `.pipeline/qa-state/` directory exists
- `scripts/intent.py` is executable and handles all subcommands
- Intent start/done cycle works: start → show (open) → done → show (no open)
- `.pipeline/config.json` is in `.gitignore`

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_intent.py::test_intent_start` — starting an intent writes entry with correct fields
- `tests/test_intent.py::test_intent_done` — marking done sets `done: true` on correct entry
- `tests/test_intent.py::test_intent_show` — show returns all intents as JSON list
- `tests/test_intent.py::test_intent_open` — open returns only entries with `done: false`
- `tests/test_intent.py::test_intent_done_nonexistent` — marking done for non-existent story returns exit code 1
- `tests/test_intent.py::test_intent_json_integrity` — file is always valid JSON after any operation
