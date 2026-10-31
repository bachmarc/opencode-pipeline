# Story 32-01 — Boundary checklist + ordering invariants + bugfix completeness (prompts/template)

Status: Done
Feature: Generic Pipeline Hardening (F-032)

## Codebase Snapshot

- `docs/features/_story_template.md` — story skeleton (Status, Codebase
  Snapshot, Context/Purpose, Requirements, Developer Targets, Acceptance
  criteria, Test criteria, Tooling Gates + the debug-type comment block from
  30-02). This story adds one optional mandatory-if-applicable section
  template line.
- `agents/architect.md` — already carries (post 30-04/31-02): driver-first
  orchestration, plan_check before checkpoint, cheap-tier policy,
  no-discussion rule. This story adds the boundary-question checklist to
  the DESIGN phase guidance.
- `agents/qa-manager.md` — already carries (post 30-04/31-02): Tier D first,
  provenance, profile-conditional test rules, tier triggers. This story adds
  the bugfix-completeness rule and the invariant-section check line.
- `tests/test_agent_profile_awareness.py` (30-04) and
  `tests/test_architect_model_policy.py` (31-02) — prompt self-check test
  files; same test area, extend or add sibling test file (verify via grep).

## Context / Purpose

VirtOffice retrospective (bug-retrospective.md): the biggest bug clusters
were lifecycle ordering (~35%) and underspecified boundary behavior (~25%) —
both are generic properties of stateful software, and both were planning
gaps: nothing asked the architect for ordering invariants or boundary
answers, so the developer had no spec to violate. Separately, fixes landed
without regression nets (resolution pattern §4.1: the mature 32→33→34
pattern should become the rule). plan_check (30-05) already FAILs on
unresolved `[NEEDS CLARIFICATION]` markers — but nothing GENERATES them for
boundary cases. This story makes the checklist and the invariant section
part of the planning vocabulary.

## Requirements

1. `docs/features/_story_template.md`: add ONE commented section hint
   `## Ordering & Recovery Invariants (mandatory for lifecycle stories)` to
   the Test criteria area — applicability is the architect's judgment
   (multi-step lifecycles: start/stop, publish/subscribe, join/leave,
   transactional sequences), no trigger-word automation. The hint is an HTML
   comment (same class as the existing snapshot comments — it persists
   verbatim into generated stories, harmless, no plan_check impact);
   `create_story.py` is NOT modified by this story. Normal story rendering
   stays unchanged.
2. `agents/architect.md` design-phase guidance gains the **boundary
   checklist** (generic, verbatim five questions):
   - What happens on degenerate/empty inputs or states?
   - What is visible in intermediate states during transitions?
   - What is the abort/error semantics mid-flight (stop, rollback)?
   - What happens on repeat/reconnect — is it idempotent?
   - Which environments does it run in (and which combination matters)?
   Plus the rule: unclear or undecided answers MUST become
   `[NEEDS CLARIFICATION: ...]` markers in the story (plan_check enforces
   resolution before dev). Plus: lifecycle stories get the Ordering &
   Recovery Invariants section (see template hint).
3. `agents/qa-manager.md` gains TWO rule lines:
   - **Bugfix completeness:** a bugfix story is PASS only if a regression
     test exists that would have caught the fixed bug (repro of the
     failure) — provenance tier-k judgment.
   - **Invariant section:** for stories declaring lifecycle scope, the
     Ordering & Recovery Invariants section must exist and be tested —
     missing → FAIL (not BLOCKED; the template hint names it).
4. NO code changes, NO checker changes, NO new scripts. Prompt/template
   work only.

## Developer Targets (exactly, no more / no less)

- `docs/features/_story_template.md` — the one section hint.
- `agents/architect.md` — boundary checklist block (verbatim five
  questions) + marker-generation rule + invariant-section rule.
- `agents/qa-manager.md` — the two rule lines.
- Extend/add sibling tests pinning the new prompt content (grep-locate
  existing prompt tests first; list them in `affects:`).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `agents/architect.md` contains the five boundary questions verbatim +
  the marker-generation rule (`[NEEDS CLARIFICATION` referenced).
- `agents/qa-manager.md` contains the bugfix-completeness rule and the
  invariant-section FAIL rule (grep: `regression test`,
  `Ordering & Recovery Invariants`).
- `docs/features/_story_template.md` contains the section hint; existing
  constant sections and the debug-type comment block unchanged.
- All framework self-check tests green.

## Test criteria (must exist BEFORE implementation)

- `tests/test_prompt_boundary_rules.py` (new): reads the three files and
  asserts — (a) the five boundary questions present in architect.md,
  (b) `[NEEDS CLARIFICATION` marker-generation rule present,
  (c) bugfix-completeness rule in qa-manager.md,
  (d) `Ordering & Recovery Invariants` hint in the story template,
  (e) template constant sections byte-unchanged vs main.
- Existing prompt self-checks stay green.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest per `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black)