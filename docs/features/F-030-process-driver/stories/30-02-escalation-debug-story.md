# Story 30-02 — Escalation rules + debug story type

Status: Planned
Feature: Process Driver (F-030)

## Codebase Snapshot

- `scripts/driver.py` — created by 30-01 (if 30-01 is not merged yet, both
  stories build on the SAME story file's targets; this story extends the pure
  core and CLI, no conflict on the same branch).
- `scripts/create_story.py` — `get_next_story_id(feature_dir)` ~line 26, usage
  `create_story.py <feature-name> <slug> [--feature <feature-id>]`, copies
  `_story_template.md` and fills machine fields. This story adds a `--type
  debug` mode with a different body skeleton.
- `docs/features/_story_template.md` — the current story skeleton (Status,
  Codebase Snapshot, Context/Purpose, Requirements, Developer Targets,
  Acceptance criteria, Test criteria, Tooling Gates).
- `STORIES.md` — phase index at the bottom; Phase 30 will be appended with
  these stories by the regression-checked entry format (title/status/trace).

## Context / Purpose

When a developer fails QA repeatedly, replaying the same cheap model in
circles wastes cycles — an LLM would have to "decide" to escalate, which is
exactly the unreliable path this feature removes. The historically PROVEN
escape pattern (previous project): write a **debug story** — an investigation
story the cheap developer executes (explore the situation, report findings,
uncover additional bugs/gaps, explicitly NOT fix) — and give the architect the
findings so it can plan good stories for simple developers. This story
determines escalation RULE-based (thresholds in the profile) and makes debug
stories a first-class story type.

**Sequencing (design correction 2026-10-30):** starts only AFTER 30-01 is
merged — this story EXTENDS `scripts/driver.py`, which 30-01 creates
(same-file topology → no parallel wave; plan_check flags exactly this
conflict class).

## Requirements

1. Escalation tracking in the driver core: given story verdicts, count the
   consecutive FAIL verdicts of the CURRENT attempt series (a PASS resets the
   counter).
2. New action kinds:
   - `escalate-remedy`: consecutive fails >= `profile.escalation.fail_loop`
     (default 3) on one story. Payload includes
     `recommendation: "debug-story"` and
     `diagnosis: "strong-architect"` — the driver emits BOTH as a pair in the
     `reason` text, but implements nothing itself.
   - `escalated-blocked`: fails >= `profile.escalation.max_escalations`
     (default 2 escalations) already happened → action `"block-and-ask-user"`.
3. **Escalation ledger** (design correction 2026-10-30 — the driver is
   stateless, `escalated-blocked` needs a record): `create_story.py --type
   debug` APPENDS `{"story": <target story id>, "debug_story": <new id>,
   "at": <iso8601>}` to `.pipeline/escalations.json` (file created on first
   entry). The driver counts escalations per story from this ledger. The
   ledger is the ONLY escalation side effect — no model reassignment happens
   in this feature (that is F-031 policy).
4. `create_story.py --type debug <feature-name> <slug>`: story body skeleton
   for INVESTIGATION — sections "Investigation questions" (explore: what
   fails, why, reproduction, affected neighboring code), "Deliverable:
   findings report" (≤ 1 page, facts only), explicit rule "Do NOT fix code;
   do NOT change behavior". Machine fields identical to normal stories.
   Creating one appends the escalation ledger entry (req 3).
5. `docs/features/_story_template.md` gains a short comment-block template for
   the debug-story body (nothing changes for normal stories — Template
   Constancy preserved for constant sections).
6. STORIES.md phase-30 entry is appended by the merge discipline — no code
   needed for it in this story.
7. Profile `escalation` edge rules: threshold 0 → feature disabled (never
   emits escalate actions); missing `escalation` block → default values used.

## Developer Targets (exactly, no more / no less)

- Extend `scripts/driver.py` core: consecutive-fail counting + the two new
  action kinds; escalate actions sort LAST in the stable action order
  (after spawn-dev). Update the module docstring with the escalation
  semantics and the ledger source (`.pipeline/escalations.json`).
- Extend `scripts/create_story.py`: `--type debug` argument (no other
  behavior change), debug body template inline in the script, ledger append
  on debug-story creation.
- Extend `docs/features/_story_template.md`: ONLY an added HTML comment block
  at the end showing the debug-story body skeleton (zero effect on normal
  story rendering).
- Add `tests/test_driver_escalation.py` (core, pure).
- Add `tests/test_create_story_debug.py` (NEW file — design correction
  2026-10-30: the earlier draft referenced "extend
  `tests/test_create_story.py`", but that file does NOT exist in this repo —
  a ghost reference of exactly the class plan_check catches). The new test
  covers the `--type debug` skeleton AND the `.pipeline/escalations.json`
  ledger append.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- Driver action JSON: a story with 3 consecutive FAILs yields
  `escalate-remedy` with both recommendation types named; threshold 0 profile
  never produces escalate actions.
- `create_story.py --type debug` produces a story whose body mentions
  "Investigation questions", "findings report", and the not-fix rule;
  normal-type stories remain byte-identical to before (template diff only
  added comment).
- Escalation counter semantics: FAIL, FAIL, PASS, FAIL → current series is 1
  FAIL (PASS reset).
- Escalation ledger: creating a debug story for story X appends exactly one
  entry to `.pipeline/escalations.json`; a story with an existing ledger
  entry whose fail series crosses the threshold again yields
  `escalated-blocked` (not a second `escalate-remedy`).

## Test criteria (must exist BEFORE implementation)

- `tests/test_driver_escalation.py::test_three_fails_triggers_remedy`
- `tests/test_driver_escalation.py::test_pass_resets_counter` — the reset
  semantics above.
- `tests/test_driver_escalation.py::test_disabled_threshold` — `fail_loop: 0`
  emits no escalation actions.
- `tests/test_driver_escalation.py::test_max_escalations_ask_user`
- `tests/test_create_story_debug.py::test_debug_story_type` — runs
  `create_story.py --type debug` in a temp feature dir, asserts the
  investigation sections exist in the written file.
- `tests/test_create_story_debug.py::test_debug_story_appends_ledger` —
  `.pipeline/escalations.json` gains the entry; driver core yields
  `escalated-blocked` for a story with an existing ledger entry and a fresh
  fail series.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black)
