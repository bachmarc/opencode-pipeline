---
id: F-030
title: Process Driver — deterministic orchestration + profile-driven QA + escalation
status: planned
owner: ""
req: []
---

## Vision

The architect stops being the pipeline's state machine. A deterministic
driver script reads the pipeline state (intents, QA verdicts, story statuses)
plus a **per-project process profile** and computes the next required actions
(`spawn-qa`, `spawn-dev`, `merge-candidate`, `escalate`, `intent-reminder`) as
machine-readable JSON. Deviations from the default workflow ("this project
requires a different process") become **configuration entries, not
conversational improvisation** — so the driver cannot make project-specific
processes impossible.

QA is split into two tiers:

- **Tier D (deterministic, ~0 LLM tokens):** script-based process checkers
  (worktree discipline, commit-metadata consistency) run via the existing
  `qa_compress.py` checker registry and produce a machine-readable checklist.
- **Tier K (creative model):** the qa-manager reasons ONLY over what cannot be
  automated (does the test actually prove the criterion? fake parity,
  regression semantics in untested paths), using the compressed Tier D output.
  Its verdict records `provenance` (script-verified vs. LLM-judged per check).

Escalation on repeated developer failure is rule-based: the driver detects the
fail loop and emits the historically proven escape hatch — a **debug story**
(investigation story for the cheap developer) plus a strong-architect
diagnosis recommendation — instead of endless cheap retries.

## Context

**Owner findings (user session 2026-10-30):**

1. The architect currently performs two very different jobs: (a) planner,
   consultant, problem-solver for developers — this is its true value; (b)
   deterministic process work (framework housekeeping, spawning agents,
   following steps, re-arming intents forgotten around QA, planning stories
   through) — a "scrum master" job for an LLM. The result is expensive model
   tokens spent on mechanical work, and state gets LOST (two open intents from
   2026-10-15 survived ~2 weeks because nothing deterministic tracked them
   through QA interactions).
2. 23 deterministic scripts already exist (`session_recovery.py`,
   `worktree_setup.py`, `story_status.py`, `merge_if_passed.py`, `qa_route.py`,
   `intent.py`, …) — the building blocks are there. What is missing is the
   **driver** that calls them in the right order at the right time. An LLM as
   state machine is the error class the user experienced.
3. QA eats many tokens by re-reading what scripts could compute: QA repeatedly
   found "developer not working in the worktree" and "regressions in dependent
   code blocks" — the first is perfectly mechanical, the second is partially
   mechanical (via `affects:` metadata + test scope) and partially creative.
4. The framework historically WAS flexible enough to let individual projects
   deviate consistently (e.g. an In-Context-Apprentice WebUI project using
   Playwright-in-Docker instead of unit tests + fakes — producing well-tested
   code). That flexibility must survive the driver: rigs stay rigid, but the
   RIGIDITY must be config-driven (`process.json` profile), never hardcoded
  LK in prompts or scripts.
5. On dramatic developer failure, retelling the same cheap model in circles
   wastes cycles. The historically proven pattern: write a **debug story** the
   cheap developer executes (investigate situation, report findings, uncover
   additional bugs/gaps), then the architect replans good stories for simple
   developers with that information.

## Requirements (feature level)

1. **Driver core (pure, testable):** `compute_next_actions(profile, state) ->
   list[action]` — zero I/O in core; receives state as data. Actions typed as
   JSON: `{kind, story_id, reason}`.
2. **State adapter (thin):** reads `.pipeline/intent.json`,
   `.pipeline/qa-state/*.json`, story statuses; assembles the state dict for
   the core. CLI prints actions JSON; `--apply` executes only deterministic
   actions that need no LLM.
3. **Process profiles:** `.pipeline/process.json` declares the workflow
   variant (`unit-fake` default, `e2e-docker`, `hybrid`) and escalation
   thresholds. Driver behavior derives from this file. Projects deviate by
   editing the profile, not by being unserved.
4. **Tier D checkers:** `worktree_discipline` (story branch commits come from
   the story worktree) and `metadata_affects` (commit `affects:`/`symbols:`
   consistency against the actual diff) registered in `qa_compress.py`.
5. **Tier K scoping:** `qa-manager.md` rewritten to consume Tier D checklist
   output first and judge only the non-automatable remainder; verdicts carry a
   `provenance` marker per checked item.
6. **Escalation rules:** fail-loop threshold in the profile; escalation result
   is an action pair: "create a debug story for this failure" and "diagnose
   with strong architect" — clearly labeled as RECOMMENDATION, requiring no
   user gate for the diagnosis attempt itself.
7. **Debug story type:** `create_story.py --type debug` writes an
   investigation story (explore, report findings; explicitly NOT fix).

## Architecture decisions

- **Function vs connectivity:** `driver.py` core (`compute_next_actions`)
  takes a plain dict in and returns plain data out — no pathlib, no subprocess,
  no git. The CLI adapter wires real files; tests inject fixture state.
- **No spawning inside the driver (v1):** LLM spawns stay with the architect
  (subagent tool). The driver removes the *remembering* and *computing*; the
  architect makes decisions *from the driver's output only*. Autonomous
  spawning via `opencode run` is a follow-up feature candidate, NOT in scope
  here.
- **Profile is data, not code:** unknown profile keys are ignored with a
  warning, never fatal — a project checkpoint incompatibility must fail loudly
  at validation, but tolerate additive fields.
- **Regression handling split:** `metadata_affects` (deterministic) verifies
  declared dependent files; truly uncovered cross-story regressions remain
  Tier K (LLM judgment) — that is exactly where the qa-manager historically
  found real bugs.
- **qa_compress pattern reuse:** new process checkers follow the existing
  flat checker-registry pattern (check function returning `tuple[str, int]`),
  config-selected via `qa_config.json` — no new test entry point.

## Stories

- 30-01-driver-core (planned)
- 30-02-escalation-debug-story (planned)
- 30-03-tier-d-checkers (planned)
- 30-04-tier-k-scoping-prompts (planned)

## Open questions / follow-ups

- **Driver autonomy phase 2 (user discussed, deferred):** driver spawning
  dev/QA itself via `opencode run` CLI + watching QA-PASS rules autonomously.
  Deliberately deferred until the driver reliably computes correct actions.
- `scaffold_project.py` could write a default `.pipeline/process.json` per new
  project (follow-up if desired; v1 drivers read a file that scaffold/manual
  created).

## References

- User interview 2026-10-30 (architect token cost, QA token cost, dev-fail
  loops, debug-story pattern from previous project).
- Existing scripts: `session_recovery.py`, `pipeline_status.py` (state readers
  — pattern sources), `qa_compress.py` (checker registry), `intent.py`
  (intent file format), `merge_if_passed.py` (QA-PASS merge discipline).
- Related feature: F-031 model-assignment (escalation Tier reassignment uses
  `model_assign.py`).
