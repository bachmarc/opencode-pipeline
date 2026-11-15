# Story 33-03 — Driver Status Vocabulary

Status: Done (merged as 8b5b19f)
Feature: driver-trustworthiness (F-033)

## Codebase Snapshot

- `scripts/driver.py` — `_is_done()` L462 (`status.startswith("Done")`),
  `_is_qa_candidate()` L467 (exact `!= "Planned"` + prefix `_is_done` — asymmetric),
  `read_stories()` L514, `_read_status_line()` L557, `compute_next_actions()` L142,
  `read_intents()` L589; total 691 lines.
- `tests/test_driver_core.py` — 14 tests; `test_order_and_kinds` L42,
  `test_no_action_when_consistent` L91; most relevant to vocabulary changes.

## Context / Purpose

`driver.py` has two status-classification bugs producing noise:
- **D-2 (case-sensitivity):** `_is_done` uses `startswith("Done")` — `DONE (merged)` is
  not recognized, producing a false `merge-candidate`.
- **D-4 (no terminal states):** the only driver-silent states are `""` and exact `"Planned"`.
  Annotated `Planned (waiting for go)` does NOT match → false `spawn-qa`. Legitimate
  closed outcomes (reverted, dropped, superseded, dormant) must be encoded as `Done`
  (wrong) or keep making noise. The current repo already has one such status:
  `Status: Superseded by 32-03 …` → today's driver outputs a false `spawn-qa` for 29-01.
- **D-10 (intent cross-reference):** an open intent can outlive story completion by days;
  the driver should notice when a story is `Done*` and emit a closure suggestion.

Fix: replace `_is_done` + `_is_qa_candidate` with a unified `status_class()` function
using consistent prefix-match semantics, extend the driver-silent vocabulary, and
add the intent cross-reference action.

## Requirements

1. New function `status_class(status: str) -> str` in `driver.py` returns one of:
   `"done"`, `"planned"`, `"parked"`, `"closed"`, `"in_progress"`, `"unknown"`.
   - `"done"` — case-insensitive prefix `done` (e.g. `Done`, `DONE (merged)`, `Done (QA PASS, abc)`)
   - `"planned"` — case-insensitive prefix `planned` (e.g. `Planned`, `Planned (waiting for go)`)
   - `"parked"` — case-insensitive prefix match on any of: `parked`, `dormant`,
     `eingestellt`, `on hold` (driver-silent; work paused, not cancelled)
   - `"closed"` — case-insensitive prefix match on any of: `closed`, `reverted`,
     `dropped`, `superseded`, `cancelled` (driver-silent; work will not be merged)
   - `"in_progress"` — everything else non-empty (QA candidate)
   - `"unknown"` — empty string
2. `_is_done(status)` and `_is_qa_candidate(status)` are replaced by `status_class()`
   calls internally; their external names may be kept as thin wrappers for test backward
   compat or removed (tests updated accordingly).
3. Both `"parked"` and `"closed"` statuses are driver-silent: no `spawn-qa`, no
   `merge-candidate` action generated for them.
4. **D-10 intent cross-reference:** when an open intent exists for a story and that
   story's `status_class` is `"done"`, `compute_next_actions()` emits an
   `intent-closure-suggested` action:
   `{"kind": "intent-closure-suggested", "story_id": "<id>", "intent_id": "<id>",
     "reason": "story appears done — run intent.py done <intent_id>"}`.
5. The `status_class` function is documented with a docstring listing all recognized
   prefixes and their class.

## Developer Targets (exactly, no more / no less)

- `scripts/driver.py`:
  - Add `status_class(status: str) -> str` function with full docstring.
  - Replace `_is_done` and `_is_qa_candidate` body with `status_class()` calls
    (or deprecate them as one-line wrappers — tests decide).
  - In `compute_next_actions()`: add `intent-closure-suggested` logic (D-10).
  - Add `"intent-closure-suggested"` to `_ACTION_ORDER` list.
  - Update module docstring to mention the status vocabulary.
- `tests/test_driver_core.py`:
  - `test_status_class_done_variants` — `Done`, `DONE (merged)`, `done (qa pass, abc)` → `"done"`.
  - `test_status_class_planned_variants` — `Planned`, `Planned (waiting for go)` → `"planned"`.
  - `test_status_class_parked_variants` — `Parked`, `Dormant`, `Eingestellt`, `On Hold` → `"parked"`.
  - `test_status_class_closed_variants` — `Closed`, `Reverted`, `Dropped`, `Superseded ...`, `Cancelled` → `"closed"`.
  - `test_parked_story_no_driver_action` — story with `Status: Parked` produces no action.
  - `test_closed_story_no_driver_action` — story with `Status: Superseded by 32-03 …` produces no action.
  - `test_intent_closure_suggested_when_story_done` — open intent for a `Done` story emits `intent-closure-suggested`.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `status_class()` exists and is importable from `driver.py`.
- `Status: Superseded by 32-03 …` (29-01) produces no driver action (confirmed by `test_closed_story_no_driver_action`).
- `Status: DONE (QA-PASS merged)` is recognized as done (D-2 fix).
- `Status: Planned (waiting for go)` is driver-silent (D-4a fix).
- `intent-closure-suggested` action emitted when open intent + `Done` story.
- All 14 existing `test_driver_core.py` tests still pass (or updated for vocabulary rename).

## Test criteria (must exist BEFORE implementation)

- `test_status_class_done_variants` — all case/annotation variants of `Done` → `"done"`.
- `test_status_class_planned_variants` — annotated Planned → `"planned"` (not `"in_progress"`).
- `test_status_class_parked_variants` — each parked prefix → `"parked"`.
- `test_status_class_closed_variants` — `Superseded …` → `"closed"` (covers the 29-01 real case).
- `test_parked_story_no_driver_action` — no action for parked story.
- `test_closed_story_no_driver_action` — no action for closed/superseded story.
- `test_intent_closure_suggested_when_story_done` — `intent-closure-suggested` emitted.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy)
- [ ] Format check clean (black)
- [ ] Audit clean — n/a (no package registry)
