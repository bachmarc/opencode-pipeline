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

## Requirements

1. `agents/architect.md` policy flip:
   - Architect runs on the CHEAP tier by default (locally configured).
   - Strong tier is applied ONLY at defined escalation points:
     (a) planning checkpoint with genuinely new/dangerous design territory,
     (b) `BLOCKED_Design` repair after QA, (c) driver `escalate-remedy`
     diagnosis recommendation (F-030). Otherwise stay cheap.
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
4. Backwards texture: the existing developer-model line (`agents.developer`
   mass-model note) stays untouched — this is architect-scoped only.

## Developer Targets (exactly, no more / no less)

- `agents/architect.md`: replace the strong-model policy line with the new
  policy block (cheap default + 3 escalation points + assignment script
  reference) and ADD the no-discussion paragraph. Update any self-referential
  description line mentioning the model tier if present.
- Update affected prompt-structure self-check tests (grep-locate first; e.g.
  tests asserting the old "only as fallback" policy line).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `agents/architect.md` contains the strings: `cheap tier`,
  `escalate-remedy`, `BLOCKED_Design`, `model_assign.py`, and the prohibition
  paragraph (case-sensitive grep).
- No changes to `agents/developer.md`, `agents/qa-manager.md`, templates.
- All framework self-check tests green.

## Test criteria (must exist BEFORE implementation)

- `tests/test_architect_model_policy.py` (new, file-reading):
  - `test_cheap_default_stated` — file states the cheap-tier default for the
    architect.
  - `test_escalation_points_referenced` — exact strings `(a) planning`,
    `escalate-remedy`, `BLOCKED_Design`, `model_assign.py` present.
  - `test_no_discussion_rule_present` — the prohibition paragraph exists
    (matching a normalized whitespace substring).
- Existing test(s) pinning the old policy line updated in the SAME commit.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest)
- [ ] Lint clean (ruff)
- [ ] Format check clean (black)
