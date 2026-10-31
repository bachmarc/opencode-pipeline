# Story 32-02 — Main health (post-merge suite check) + driver stale-planned

Status: Planned
Feature: Generic Pipeline Hardening (F-032)

## Codebase Snapshot

- `scripts/merge_if_passed.py` — merge gate: extract_story_id (~line 50),
  check_qa_pass (~line 64), check_documenter_commit (~line 82),
  merge_branch `git merge --no-ff` (~line 126), main() gate sequence
  (~line 150, gate body 161–183): QA-PASS → documenter commit → merge →
  output JSON. This story appends a post-merge step after `merge_branch`
  success.
- `scripts/driver.py` — (30-01/30-02, current) pure core
  `compute_next_actions`, action kinds: intent-reminder, spawn-qa,
  merge-candidate, spawn-dev, escalate-remedy, escalated-blocked
  (escalation kinds last, `_ACTION_ORDER`), `read_escalations()` adapter,
  CLI `next`/`validate`, read-only. This story adds one action kind.
- `scripts/qa_compress.py` — checker registry incl. `pytest_check`
  (~line 98) with `--fast-mode` scope selection (22-x); the post-merge
  check reuses the configured checker list, NOT a hardcoded runner.
- `tests/test_merge_if_passed.py` — 6 subprocess tests via `sys.executable`
  (30-06). `tests/test_driver_core.py` / `test_driver_escalation.py` —
  core action tests incl. stable-order test (30-02).

## Context / Purpose

This session produced two generic stability findings: (a) **main decay** —
8 pre-existing test FAILs on main survived ~2 weeks and blocked every
wave-1 merge before anyone noticed (each developer had to re-verify via
git stash); (b) **phantom stories** — 29-01 existed as a Planned story doc
for weeks with no intent, no worktree, no implementation, and nothing
surfaced it. Both are deterministically detectable: the merge gate is the
single choke point where main changes, and the driver already computes
"what needs attention" from story statuses. This story adds both checks —
zero LLM tokens, pure script work.

## Requirements

1. **Post-merge main health in `merge_if_passed.py`:** after a successful
   merge, run the configured test suite (the `qa_config.json` checker list,
   same selection logic the QA gate uses) on main.
   - Suite green → output gains `"post_merge": {"suite": "PASS"}` (exit 0
     as today).
   - Suite FAIL → output `"post_merge": {"suite": "FAIL", "note": "main is
     red — create a fix story immediately (30-06 pattern); do NOT merge
     further stories onto red main"}` — exit **3** (new distinct code),
     NO rollback of the merge (rollback would destroy the merge-commit
     trail; the error is loud, the follow-up is a story).
   - Suite runners unavailable (e.g. missing binary) → `"post_merge":
     {"suite": "SKIPPED", "reason": ...}` exit 0 (fail-open, one line in
     the note).
2. **`stale-planned` action in `scripts/driver.py`:** new action kind for
   stories with `Status: Planned` older than
   `profile.planning_max_age_days` (default 14) with NO open intent for
   that story and NO registered worktree for it. Reason text: "planned
   story untouched — re-plan, implement, or drop".
   - `stale-planned` sorts before the escalation kinds (after spawn-dev),
   extending `_ACTION_ORDER` — existing order tests must be extended, not
   broken.
   - Story age source: file mtime of the story file (deterministic,
   stdlib); no git history parsing.
   - Threshold 0 disables (same convention as escalation thresholds).
3. NO changes to `worktree_setup.py`, `plan_check.py`, or the merge gate
   sequence (QA-PASS + documenter checks stay exactly as-is).

## Developer Targets (exactly, no more / no less)

- `scripts/merge_if_passed.py` — post-merge suite step (reusing the
  qa_config checker selection), new exit code 3, JSON contract per req 1.
- `scripts/driver.py` — `stale-planned` action kind + threshold + order.
- `tests/test_merge_if_passed.py` — extend: green-suite merge (exit 0 +
  post_merge PASS), red-suite merge (exit 3 + note), unavailable runner
  (SKIPPED, exit 0).
- `tests/test_driver_core.py` — extend/add: stale-planned emission
  (old + no intent + no worktree), suppression (open intent OR worktree
  OR fresh), threshold-0 disabled, stable order position.
- Module docstrings updated (both scripts) — source of truth.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- Post-merge suite runs against the configured checker list (verify: red
  fixture suite → exit 3, note present; green → exit 0 with PASS field).
- No rollback performed on FAIL (merge commit stays).
- `stale-planned` emitted exactly when age > threshold AND no open intent
  AND no worktree; each suppression factor tested.
- Existing action order unchanged; new kind positioned before escalate
  kinds (test proves the full stable order).
- All existing merge-gate tests (6) still green.

## Test criteria (must exist BEFORE implementation)

- `tests/test_merge_if_passed.py::test_post_merge_green_exit0`
- `tests/test_merge_if_passed.py::test_post_merge_red_exit3_note` — note
  text names the 30-06 fix-story pattern; merge commit still present
  (no rollback).
- `tests/test_merge_if_passed.py::test_post_merge_runner_missing_skipped`
- `tests/test_driver_core.py::test_stale_planned_emitted`
- `tests/test_driver_core.py::test_stale_planned_suppressed_by_intent_or_worktree_or_fresh`
- `tests/test_driver_core.py::test_stale_planned_threshold_zero_disabled`
- `tests/test_driver_core.py::test_action_order_includes_stale_planned`

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest per `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black)