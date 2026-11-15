# Story 34-01 — Loop Protection Prompts

Status: Done (merged as 6a07cfe)
Feature: developer-loop-protection (F-034)

## Codebase Snapshot

- `agents/developer.md` — 49 lines. Step-tracking rule at L20; fix loop ("Run suite green
  again → back to QA") at L49. No step budget or anti-loop limit defined.
- `agents/architect.md` — 221 lines. Orchestration guidance around L160–180 (spawn
  patterns). No item-wise spawn guidance for exploration/verification work.
- `templates/AGENTS.md` — 117 lines. Environment Constraints pattern mentioned in the
  scaffold story hint but not as a general developer-session recommendation.
- `tests/test_developer_prompt.py` — 2 tests (L13, L64). New tests go here.

## Context / Purpose

VirtOffice session 2026-10-25 (story 26-09, GLM-5.3-Flash developer): a long-running
exploration subagent looped chaotically; the run needed 4 attempts with server restarts.
OpenCode's `agents.developer.steps` cap removes tools at the budget and forces a summary —
a bounded agent cannot loop forever. Item-wise spawn discipline (one matrix item per
subagent) limits restart loss. Anti-loop rules stop the agent from repeating the same
failing action more than a few times. These are prompt/config doc changes only; no
Python code is involved. See TODO.md → T-001.

## Requirements

1. `agents/developer.md` gains a hard anti-loop rule: "Never repeat the same failing
   action more than 2–3 times. On the third failure, mark the item DEFERRED with a
   one-line diagnosis and move on."
2. `agents/developer.md` gains a step-budget recommendation: "Configure
   `agents.developer.steps` (e.g. 60–80) in the project-local `opencode.jsonc` to cap
   runaway loops. OpenCode removes tools at the cap and forces a summary."
3. `agents/architect.md` gains item-wise spawn guidance in the Phase 3 orchestration
   section: for long exploration or multi-item verification work, cut into item-level
   subagent spawns (one item or a small group per spawn) with incremental-commit
   discipline so aborts and restarts lose at most one item of work.
4. `templates/AGENTS.md` mentions `agents.developer.steps` as a recommended entry in
   the project-local `opencode.jsonc` (one line, in the environment / tooling section).
5. Module/file headers updated in every changed file.

## Developer Targets (exactly, no more / no less)

- `agents/developer.md`:
  - Add anti-loop rule (requirement 1) in the Prohibitions or Rules section.
  - Add step-budget recommendation (requirement 2) near the workflow section.
  - Update file header comment if present (otherwise the opening prose counts).
- `agents/architect.md`:
  - Add item-wise spawn guidance (requirement 3) in Phase 3 Orchestration.
- `templates/AGENTS.md`:
  - Add one-line step-budget note (requirement 4) in the environment/tooling area.
- `tests/test_developer_prompt.py`:
  - `test_developer_prompt_has_anti_loop_rule` — developer.md contains the keyword
    "DEFERRED" (or "deferred") AND a phrase matching "same failing action" or equivalent.
  - `test_developer_prompt_has_step_budget_recommendation` — developer.md contains
    "agents.developer.steps".
  - `test_architect_prompt_has_item_wise_spawn_guidance` — architect.md contains
    "item-level" or "item-wise" in the Phase 3 section.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `agents/developer.md` contains an anti-loop rule with the DEFERRED concept.
- `agents/developer.md` contains a step-budget recommendation referencing
  `agents.developer.steps`.
- `agents/architect.md` contains item-wise spawn guidance in Phase 3.
- `templates/AGENTS.md` mentions `agents.developer.steps`.
- All 3 new tests pass; existing 2 tests unaffected.
- No concrete model/provider names introduced in any portable file.

## Test criteria (must exist BEFORE implementation)

- `test_developer_prompt_has_anti_loop_rule` — `developer.md` contains the anti-loop
  rule (DEFERRED keyword or equivalent phrase present).
- `test_developer_prompt_has_step_budget_recommendation` — `developer.md` contains
  `agents.developer.steps`.
- `test_architect_prompt_has_item_wise_spawn_guidance` — `architect.md` contains
  item-wise spawn guidance text.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean — n/a (Markdown only; no Python changes)
- [ ] Typecheck clean — n/a
- [ ] Format check clean — n/a
- [ ] Audit clean — n/a
