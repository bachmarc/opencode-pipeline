# Story <ID> — <Title>

Status: Planned | In Progress | Done
Feature: <feature-name> (<feature-id>)

## Codebase Snapshot

<!-- Filled by Architect at decomposition time. Lists affected files, relevant function
     signatures, and existing tests near the change. Developer reads this first.
     Omit only for trivial one-liners with no existing code to navigate. -->

- `<file>` — <what is in it that is relevant: function name, line range, what it does>
- `<test file>` — <which existing tests cover adjacent code>

## Context / Purpose

<Why does this story exist? What problem does it solve? Self-contained — no external references needed>

## Requirements

<What must be true when this story is done? Functional requirements in the story's own words>

**Guidance for architects:** If any requirement is ambiguous or not explicitly decided by the user, mark it with `[NEEDS CLARIFICATION: <specific question>]` instead of guessing. The user resolves these at the review checkpoint before implementation starts.

## Developer Targets (exactly, no more / no less)

- <Concrete changes — file by file>
- Update docstrings and module headers in every file you change — code documentation is the source of truth.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- <Deterministically verifiable criteria>

## Test criteria (must exist BEFORE implementation)

- <Tests written first — file, test name, expected behavior>

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean (e.g. `eslint`, `rubocop`, `ruff`)
- [ ] Typecheck clean (e.g. `tsc`, `mypy`) — if typed language
- [ ] Format check clean (e.g. `prettier`, `black`) — if formatter configured
- [ ] Audit clean (e.g. `npm-audit`, `bundler-audit`) — 0 high/critical

<!-- DEBUG-STORY-BODY-TEMPLATE (Story 30-02, F-030) — reference only.

     Skeleton for INVESTIGATION stories: create_story.py --type debug
     generates this body inline and appends the escalation ledger entry to
     .pipeline/escalations.json. Normal stories never contain this block:
     create_story.py strips it here, so normal story output stays
     byte-identical to the pre-30-02 template.

     # Story <ID> — <Title>

     Status: Planned
     Feature: <feature-name> (<feature-id>)

     ## Codebase Snapshot

     (failing story, its QA verdict history, affected files/tests)

     ## Context / Purpose

     (QA failure or fail loop that triggered the investigation)

     ## Investigation questions

     What fails (verdicts, failing checkers, error output), why (root cause
     with file/line evidence), deterministic reproduction (commands,
     fixtures), affected neighboring code (callers, dependent tests, docs).

     ## Requirements

     Answer every investigation question with facts; uncover additional
     bugs and gaps in the affected area. Do NOT fix code; do NOT change
     behavior.

     ## Deliverable: findings report

     At most 1 page, facts only: symptoms, root cause, affected files,
     reproduction steps, additional bugs and gaps uncovered.
-->
