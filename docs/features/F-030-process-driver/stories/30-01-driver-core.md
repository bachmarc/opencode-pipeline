# Story 30-01 — Driver core: process profiles + compute next actions

Status: Planned
Feature: Process Driver (F-030)

## Codebase Snapshot

- `scripts/pipeline_status.py` — existing state reader: `read_qa_state()` at
  ~line 233 (reads `.pipeline/qa-state/*.json`), open intents reader at ~line
  251 (reads `.pipeline/intent.json`). Pattern source for the state adapter;
  driver reuses these file locations but does NOT import pipeline_status.py
  (core stays I/O-free).
- `scripts/session_recovery.py` — `get_open_intents()` ~line 51, QA state
  extraction ~line 159, pipeline dir resolution ~line 234. Reference for the
  intent.json shape: `{"intents": [{"story_id", "agent", "step",
  "started_at", "done"}]}`.
- `scripts/qa_route.py` + `.pipeline/qa-state/*.json` — verdict files keyed by
  story id with `verdicts: [{verdict, branch, commit, tests, timestamp}]`.
- `scripts/intent.py` — intent start/done commands; the driver's `--apply`
  mode shells out to nothing but may emit actions that the architect fulfills
  via `intent.py done`.
- `tests/` — framework self-checks read repo files and run scripts via
  subprocess; no test currently covers pipeline_status/session_recovery state
  reading (pattern: `tests/test_framework.py` style).

## Context / Purpose

Today the architect must remember to check intents, QA verdicts and story
statuses and derive next steps from memory — an LLM as state machine. Evidence:
two intents (`F-027` planning, `27-02` dev implementing) stayed open for ~2
weeks. This story creates the deterministic replacement: a driver whose PURE
core computes the next required actions from data, plus a thin CLI adapter
that assembles the state from `.pipeline/`. The process VARIANT (default vs.
project-specific workflow) comes from a `process.json` profile so project
deviations are configuration, never improvisation.

## Requirements

1. `scripts/driver.py` with a pure core function
   `compute_next_actions(profile: dict, state: dict) -> list[dict]`.
   - Core imports NOTHING besides stdlib typing — state is a plain dict:
     stories: `[{id, status}]`, qa_state: `{story_id: [verdict...]}`,
     intents: `[intent...]`, worktrees: `[names...]`.
   - Profile keys consumed by this story: `workflow: "default"|"custom"`,
     `test_strategy: "unit-fake"|"e2e-docker"|"hybrid"`, plus arbitrary
     additional keys which the core IGNORES silently (extensibility rule).
2. Computed action kinds (each `{kind, story_id?, reason}`):
   - `intent-reminder`: an intent exists that is older than
     `profile.intent_max_age_hours` (default 72) and still open.
   - `spawn-qa`: story status is dev-done/committed but no QA verdict exists.
   - `merge-candidate`: latest QA verdict for the story is PASS but the story
     is not Done.
   - `spawn-dev`: story status Planned/In-Progress with a failed QA verdict
     present (fail loop detection deferred to 30-02; here single FAIL maps to
     `spawn-dev`).
   - `no-action`: state is fully consistent (never omitted — reported
     explicitly).
3. Multiple findings produce multiple actions, in a STABLE order:
   intent-reminder, spawn-qa, merge-candidate, spawn-dev (deterministic for
   tests).
4. Profile validation: missing `workflow` key → driver exits code 2 with a
   clear error (fails loudly). Unknown extra keys → stdout warning, still
   valid.
5. CLI:
   - `driver.py next` — loads state + profile, prints actions as JSON array,
     exit 0 regardless of action kinds.
   - `driver.py next --apply` — beyond printing, executes only actions with a
     deterministic side effect that needs no LLM: for `intent-reminder` it
     writes nothing (report-only in this story); `--apply` therefore only
     re-reads state and exits 0 — full apply behavior lands with 30-02.
   - `driver.py validate` — validates `process.json` only, prints JSON
     `{result: PASS}` or detailed error, exit 0/1.
6. `--profile <path>` flag (default `.pipeline/process.json`); a missing
   profile file yields the built-in default profile
   (`workflow=default`, `test_strategy=unit-fake`, `intent_max_age_hours=72`).

## Developer Targets (exactly, no more / no less)

- Create `scripts/driver.py`: pure core function + CLI adapter + module
  docstring documenting profile keys, action kinds, and the intent of "no LLM
  required to decide".
- Create `tests/test_driver_core.py` covering the core ONLY (pure function,
  no filesystem) and `tests/test_driver_cli.py` covering CLI behavior against
  a fixture temp repo (`.pipeline/` populated, fake `process.json`).
- Update `scripts/README`-adjacent docs if a scripts index exists — verify
  with `grep -r "pipeline_status" scripts/ docs/` and only touch a file if it
  lists scripts (keep list entries consistent).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `driver.py validate` PASSes the schema of a valid profile and FAILs (exit 1)
  on a profile without `workflow`, with a message naming the missing key.
- Unknown profile keys produce a warning on stdout but exit 0.
- Given a fixture state (1 stale intent, 1 story with QA PASS not merged, 1
  story FAIL, no other issues), `driver.py next` prints exactly 4 actions in
  the defined order and well-formed JSON.
- Pure core has no `pathlib`/`subprocess`/imports beyond typing/stdlib data
  structures (self-check via test asserting module imports).

## Test criteria (must exist BEFORE implementation)

- `tests/test_driver_core.py::test_order_and_kinds` — fixture state yields
  intent-reminder, spawn-qa, merge-candidate, spawn-dev in exactly that order.
- `tests/test_driver_core.py::test_no_action_when_consistent` — clean state
  yields exactly `[{"kind": "no-action"}]`.
- `tests/test_driver_core.py::test_stale_intent_threshold` — intent older than
  threshold → reminder; fresh intent → no reminder.
- `tests/test_driver_core.py::test_unknown_profile_keys_ignored` — extra keys
  do not change actions and do not raise.
- `tests/test_driver_cli.py::test_cli_validate_pass_fail` — fixture profile
  valid → exit 0 `{"result": "PASS"}`; missing `workflow` → exit 1 with key
  name in output.
- `tests/test_driver_cli.py::test_cli_next_fixture_repo` — temp repo with
  `.pipeline/` populated produces the 4-action JSON on stdout.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest per `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured for scripts/
- [ ] Format check clean (black)

---

## Notes

- Escalation (fail loops) and debug-story output belong to 30-02.
- Read-only v1: `next` never mutates state; this keeps the story isolated and
  reviewable.
