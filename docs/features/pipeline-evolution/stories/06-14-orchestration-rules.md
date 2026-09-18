# Story 06-14 — Orchestration rules and QA self-enforcement

Status: Planned
Traceability: NFR-004 → Design §13

## Definition

Add orchestration discipline rules to the architect prompt and QA self-enforcement to
the qa-manager prompt. These rules prevent three observed anti-patterns: batch-QA
(multiple stories in one QA agent), redundant pytest runs by the architect, and
unnecessary waiting for all developers before starting QA.

Also document the orchestration principles in design.md.

## Development goal

After this story, the architect prompt contains explicit orchestration rules for Phase 3
(implementation), the QA-manager refuses batch assignments, and design.md documents the
orchestration principles.

## Developer Targets (exactly, no more / no less)

- Update `agent/architect.md` — add a new section `## Phase 3 Orchestration (MANDATORY)` 
  after the existing "Output after Phase 1+2" section, with these rules:
  1. "Start QA for each story individually as soon as its developer is done. Do NOT wait
     for other developers to finish. Do NOT batch multiple stories into one QA agent."
  2. "Do NOT run pytest yourself in worktrees. Pytest is exclusively the QA-Manager's job.
     Your only verification before QA is checking that the developer reported success."
  3. "Minimize your own token usage in Phase 3. Use scripts for all deterministic work
     (worktree_setup, story_status, merge_if_passed). Your value in Phase 3 is decision-making
     on BLOCKED situations and user dialogue — not mechanical orchestration."
  4. "When a technical decision requires determinism (concurrency, state management, format
     consistency), proactively recommend script-based solutions. Do not accept LLM-only
     approaches for operations that need atomicity."

- Update `agent/qa-manager.md` — add a self-enforcement rule to the "## Your Assignment"
  section:
  "**Single-story enforcement:** You check exactly ONE story per invocation. If your prompt
  contains multiple stories, check only the first and return FAIL with reason:
  'Batch-QA forbidden — invoke separately per story.' This prevents context degradation
  on cheap models."

- Update `docs/design.md` — add a new section `## 14. Orchestration principles (NFR-004)`
  documenting:
  - Phase 3 token optimization (architect minimizes own usage, delegates to scripts)
  - Pipeline streaming (QA starts per story, not per wave)
  - QA self-enforcement (single-story rule)
  - Determinism boundary (architect must flag operations needing scripts)

## Acceptance criteria (checked by qa-manager)

- `agent/architect.md` contains "Phase 3 Orchestration" section with all 4 rules
- `agent/qa-manager.md` contains "Single-story enforcement" rule
- `docs/design.md` contains "Orchestration principles" section
- No concrete model/provider names introduced
- Existing tests still pass

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_orchestration_rules.py::test_architect_has_orchestration_section` — architect.md contains "Phase 3 Orchestration"
- `tests/test_orchestration_rules.py::test_architect_no_batch_qa_rule` — architect.md contains "Do NOT batch"
- `tests/test_orchestration_rules.py::test_architect_no_own_pytest_rule` — architect.md contains "Do NOT run pytest yourself"
- `tests/test_orchestration_rules.py::test_qa_single_story_enforcement` — qa-manager.md contains "Single-story enforcement" and "Batch-QA forbidden"
- `tests/test_orchestration_rules.py::test_design_orchestration_section` — design.md contains "Orchestration principles"
- `tests/test_orchestration_rules.py::test_no_model_names` — no model names introduced in changed files
