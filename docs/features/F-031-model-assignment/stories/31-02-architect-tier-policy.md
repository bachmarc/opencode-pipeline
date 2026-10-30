# Story 31-02 — Architect tier policy flip + no-discussion rule

Status: Planned
Feature: Model Assignment (F-031)

## Codebase Snapshot

- `agents/architect.md` — current session prompt. Model-related line:
  "**Cut stories so cheap mass models (locally configured via
  `agents.developer.model`) can implement them … Expensive/strong model only
  as fallback (locally via `agents.architect.model`), not for mass
  implementation**" — the policy line this story flips. Story planning /
  review checkpoint sections establish where escalation points live (planning
  checkpoint, BLOCKED_Design handling under "Autonomous Design Repair").
- `agents/agent-profile` self-checks: `tests/` contains prompt-structure
  self-checks (see `tests/test_agent_profile_awareness.py` created by 30-04 —
  same test area; 30-04 may not be merged yet, coordinate via branch order:
  this story is Wave 2 alongside 30-04 and must not conflict on the same
  files — verify after rebase of main).
- `docs/features/F-031-model-assignment/feature.md` — policy rationale and
  escalation points referenced by this story.

## Context / Purpose

The user's architecture tests showed the cheap tier suffices ~99% for the
architect role — the strong tier is only justified at defined escalation
points. Today's prompt prescribes the opposite default for the architect
("strong model only as fallback" implies running strong by default) and says
nothing about how model CHANGE requests are handled, so they turn into
token-burning discussions. This story flips the policy and hard-codes the
no-discussion rule.

**Sequencing (same-file discipline):** starts only AFTER 30-04 is merged —
both stories edit `agents/architect.md`.

## Requirements

1. `agents/architect.md` policy flip:
   - Architect runs on the CHEAP tier by default (locally configured).
   - Strong tier is applied ONLY at defined escalation points:
     (a) **planning audit** — strong-model review of planning artifacts
     (stories + `plan_check.py` output) before dev start; REQUIRED when
     plan_check reports unresolved conflict candidates or the feature
     introduces new process mechanics (new script category, new workflow),
     OPTIONAL for routine replans (user choice at checkpoint),
     (b) `BLOCKED_Design` repair after QA,
     (c) driver `escalate-remedy` diagnosis recommendation (F-030).
     Otherwise stay cheap: weak models run the continuous loop
     (plan→dev→QA→merge), and only these triggers pull in strong tokens.
   - The reassignment mechanism is `model_assign.py --apply` (31-01) — one
     line, no dialogue.
2. No-discussion rule (verbatim paragraph in `agents/architect.md`):
   "Model/provider assignment changes are NEVER discussed, explained,
   justified, or recommended. When the user states an assignment, the
   architect's entire allowed reaction is: apply via the assignment script
   (or acknowledge the user applied it) and confirm the resulting mapping in
   ONE line. Suggestions about 'how' or 'where' to put it are prohibited."
3. Escalation points reference must be consistent with F-030 terminology
   (`escalate-remedy`, `BLOCKED_Design`) — use those exact strings.
4. **QA tier triggers** (design decision 2026-10-30, audit of cost vs
   failure asymmetry — QA is the highest-frequency agent and its false-PASS
   launders merges via `merge_if_passed.py`):
   - `agents/qa-manager.md` gains a tier-trigger paragraph — role-abstract:
     tier SEMANTICS only, NO model/provider names in the prompt (concrete
     models live in the local map, applied via `model_assign.py`):
     - CHEAP tier is the QA default (routine passes, fix-loop round 2+
       re-verifications).
     - STRONG tier QA passes REQUIRED at: (a) the FIRST QA pass of a story
       introducing new process mechanics (new script category, new checker
       type, new workflow — real case: this Phase 30/31 wave itself),
       (b) `BLOCKED_Design` diagnosis, (c) `max_escalations` reached /
       breaking-change final gate.
     - The qa-manager cannot reassign its own model: it emits
       `strong_review_recommended: true` in the verdict when criteria prove
       ambiguous or a design gap is suspected; the ARCHITECT applies the
       tier switch locally (`model_assign.py`) and re-runs QA — under the
       same no-discussion rule as model assignment.
5. Backwards texture: the existing developer-model line (`agents.developer`
   mass-model note) stays untouched — this is architect- and QA-scoped.

## Developer Targets (exactly, no more / no less)

- `agents/architect.md`: replace the strong-model policy line with the new
  policy block (cheap default + 3 escalation points + assignment script
  reference) and ADD the no-discussion paragraph. Update any self-referential
  description line mentioning the model tier if present.
- `agents/qa-manager.md`: ADD the tier-trigger paragraph (req 4: cheap
  default, three REQUIRED strong points, `strong_review_recommended` flag
  semantics, no-discussion application via the architect). This file is
  written by 30-04 in Wave 2 — this story runs Wave 3 AFTER 30-04 merged
  (same-file discipline, verified in the planning audit).
- Update affected prompt-structure self-check tests (grep-locate first; e.g.
  tests asserting the old "only as fallback" policy line).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `agents/architect.md` contains the strings: `cheap tier`, `planning audit`,
  `escalate-remedy`, `BLOCKED_Design`, `plan_check.py`, `model_assign.py`, and
  the prohibition paragraph (case-sensitive grep).
- `agents/qa-manager.md` contains the tier-trigger paragraph (grep: `cheap`,
  `strong_review_recommended`, `new process mechanics`) and NO model/provider
  name patterns (role abstraction).
- No changes to `agents/developer.md`, `agents/qa-manager.md`, templates.
- All framework self-check tests green.

## Test criteria (must exist BEFORE implementation)

- `tests/test_architect_model_policy.py` (new, file-reading):
  - `test_cheap_default_stated` — file states the cheap-tier default for the
    architect.
  - `test_escalation_points_referenced` — exact strings `planning audit`,
    `plan_check.py`, `escalate-remedy`, `BLOCKED_Design`, `model_assign.py`
    present.
  - `test_planning_audit_trigger_stated` — file states WHEN the strong-model
    audit is REQUIRED (unresolved plan_check conflicts / new process
    mechanics) versus OPTIONAL (routine replans).
- `tests/test_architect_model_policy.py::test_qa_tier_triggers_present` —
  `agents/qa-manager.md` mentions the cheap default, the three REQUIRED
  strong points and the `strong_review_recommended` flag; and contains NO
  model/provider name patterns (role abstraction grep).
  - `test_no_discussion_rule_present` — the prohibition paragraph exists
    (matching a normalized whitespace substring).
- Existing test(s) pinning the old policy line updated in the SAME commit.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest)
- [ ] Lint clean (ruff)
- [ ] Format check clean (black)
