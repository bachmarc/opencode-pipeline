# Story 30-04 — Tier K scoping: driver integration in agent prompts

Status: Done
Feature: Process Driver (F-030)

## Codebase Snapshot

- `agents/qa-manager.md` — Gatekeeper prompt. Line ~37: hard FAIL rule "Tests
  ... use fakes" ; lines ~47-49: fake-parity and integration-test FAIL
  criteria (currently ABSOLUTE). These must become profile-conditional.
- `agents/architect.md` — "Phase 3 Orchestration" section (current session
  prompt: worktree/spawn/merge rules, token minimization). Driver integration
  lands as an additional FIRST step in Phase 3 and "Before any work" session
  start.
- `agents/developer.md` — line ~5 description mentions "tests first, fake
  interfaces" (context only; unchanged behavior — fake rules stay for
  `unit-fake` profile projects).
- `templates/AGENTS.md` — project-level instructions: fake requirements
  (~lines 20, 33-40), QA gate description (~line 83). Gains a Process Profile
  subsection so downstream projects know `process.json` exists.
- `tests/test_framework.py` and `tests/test_check_scripts.py` — the latter
  covers `scripts/check_template_constancy.py` (CONSTANT_SECTIONS: Workflow,
  Git conventions, Languages, Prohibitions — verified 2026-10-30; the
  earlier draft named a nonexistent `tests/test_template_constancy.py` —
  ghost reference caught in audit). Both must stay green; update only where
  they pin prompt wording.

## Context / Purpose

Today `qa-manager.md` hardcodes unit+fake criteria as ABSOLUTE FAIL rules — a
project on the `e2e-docker` profile (documented real case: the user's In-Context-Apprentice
WebUI, tested via Playwright in Docker, no unit tests) would be FAILED by the
gate despite producing well-tested code — OR the QA silently adapts its
criteria by conversation, which is nondeterministic. This story wires the
tier split into the prompts: the qa-manager consumes the Tier D checklist
(driver output from 30-01/30-03, incl. new process checkers) and judges ONLY
the non-automatable remainder, marking provenance per criterion. The
architect's orchestration role is re-based on the driver.

## Requirements

1. `agents/qa-manager.md` rewrite of the checks section:
   - Step 0 (new): run/load Tier D — process/deterministic checks
     (tooling gates, Tier D checkers where selected, `driver.py next`
     findings relevant to the story) and copy their results into a
     `tier_d` section of the verdict.
   - Only NON-automatable checks remain LLM-judged: criterion-to-test
     adequacy ("does this test actually prove the acceptance criterion"),
     fake-parity reasoning, integration-vs-manual-reconstruction, semantics
     of regressions in untested dependent paths.
   - Profile-conditional criteria: under `test_strategy: e2e-docker`, the
     fake-parity FAIL rules DO NOT APPLY; instead: E2E suite green in the
     test Docker environment and ≥ 1 scenario per acceptance criterion.
     `unit-fake` keeps today's rules verbatim. Inconsistent/misdeclared
     profile (e.g. e2e-docker story but story still demands fakes) →
     `BLOCKED_Requirements` to the architect, NOT a silent adaptation.
   - Verdict JSON gains `provenance` per entry: `"tier-d" | "tier-k"`.
2. `agents/architect.md`:
   - Session start + Phase 3: first deterministic step is calling
     `driver.py next` and basing orchestration decisions ONLY on its output
     (driver decides WHO is next and WHY the architect is consulted).
   - Prohibition: no orchestration decisions from memory — if the driver
     cannot run, say so and decide EXPLICITLY with a documented reason
     (fail-open rule, one sentence).
   - **Advisory only** (design correction 2026-10-30): driver output NEVER
     authorizes a merge — merge authority remains exclusively with
     `merge_if_passed.py` (QA-PASS). The driver has no write path.
   - **Planning QA step:** before presenting ANY planning checkpoint, run
     `scripts/plan_check.py` (story 30-05) and resolve its findings —
     conflict candidates → sequential waves declared in the STORIES.md
     phase block.

**Sequencing:** starts after ALL Wave-1 stories merged: 30-01 (`driver.py`
must exist — the prompt references `driver.py next`), 30-03 (tier-D checker
names) AND 30-05 (`plan_check.py` must exist — the prompt integration
references it; audit fix 2026-10-30 added this missing dependency). The
`agents/architect.md` plan_check step ships HERE (not in 30-05) — same-file
discipline.
3. `templates/AGENTS.md`: new short "Process Profile" paragraph in a
   CONSTANT-safe position (project-specifics placeholder area): projects
   declare `.pipeline/process.json` with `workflow`/`test_strategy`/
   `escalation`; the pipeline's QA gate and driver read it. No existing
   constant section text is modified.
4. Consistency sweep in existing framework self-check tests that pin the
   affected prompt wording — update assertions to the new wording, keep test
   count structure.

## Developer Targets (exactly, no more / no less)

- `agents/qa-manager.md`: steps above; docstring-equivalent header paragraph
  describing the two-tier principle.
- `agents/architect.md`: driver integration paragraph in Phase 3 and session
  start sections.
- `templates/AGENTS.md`: the ONE added "Process Profile" paragraph.
- Update the affected `tests/test_*.py` self-checks ONLY where they assert
  the old wording (verify first via grep; list them in the commit body
  `affects:`).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `agents/qa-manager.md` contains: a Tier-D-first workflow step, the
  `provenance` requirement, and profile-conditional fake rules (grep-check:
  `tier-d`, `provenance`, `e2e-docker`, `BLOCKED_Requirements`).
- `agents/architect.md` mandates `driver.py next` as first Phase-3 step and
  defines the fail-open rule.
- `templates/AGENTS.md` constant sections (workflow, git conventions,
  languages, prohibitions) are UNCHANGED — verified by the existing template
  constancy test suite passing unchanged.
- All framework self-check tests green.

## Test criteria (must exist BEFORE implementation)

- `tests/test_agent_profile_awareness.py` (new): reads `agents/qa-manager.md`
  and asserts — (a) mentions profile-conditional fake criteria with the exact
  strings `unit-fake` and `e2e-docker`, (b) mentions `provenance` and
  `tier-d`.
- `tests/test_agent_profile_awareness.py::test_architect_mentions_driver` —
  `agents/architect.md` contains `driver.py next` reference and a fail-open
  clause.
- `tests/test_agent_profile_awareness.py::test_template_process_profile` —
  `templates/AGENTS.md` contains the `process.json` mention; AND
  `tests/test_check_scripts.py` (the real constancy coverage — audit fix
  2026-10-30) still passes unchanged.
- Existing prompt self-checks (grep-located) updated to match new wording.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black)
