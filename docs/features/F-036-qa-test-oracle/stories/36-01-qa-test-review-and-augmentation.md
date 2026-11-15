# Story 36-01 — QA Test Review and Augmentation

Status: Done (merged as 4369c37)
Feature: qa-test-oracle (F-036)

## Codebase Snapshot

- `agents/qa-manager.md` — 113 lines. Current checklist: step 0 (Tier D), step 1
  (Requirements), step 2 (Tests green), step 2b (Tooling gates), step 3 (Architecture),
  step 4 (Targets), step 5 (Git hygiene). Verdict schema at L14:
  `{"status", "reason", "failed_tests", "tier_d", "provenance"}`.
  No test-review or test-augmentation step exists.
- `docs/features/_story_template.md` — `## Test criteria` section (L35–37): says
  "Tests written first — file, test name, expected behavior". No mention of QA augmentation.
- `tests/test_qa_manager_prompt.py` — 1 test (L14): `test_qa_manager_has_tooling_gates_checklist_item`.
  New tests go here.

## Context / Purpose

The QA gate currently re-runs the developer's tests. A developer who made a wrong
assumption encodes it into both implementation and tests — QA confirms it as correct.
This story makes QA a genuine test oracle:

1. **Test Review (Tier K):** QA reads the story's Test Criteria and the developer's
   test files. It evaluates: are the tests meaningful? Do they cover the spec? Are
   assumptions baked in that mirror a wrong implementation?

2. **Test Augmentation (Tier K, QA's judgment):** When gaps are found, QA writes
   additional tests — or corrects wrong ones — using the project's own conventions
   (derived from `qa_config.json`, `process.json`, and existing test patterns in the
   repo). Web app → Playwright; Python → pytest; Ruby → RSpec etc. Commit:
   `test(qa): augment coverage for <story-id>`. Scope: ONLY test files
   (tests/*, spec/*, e2e/*, playwright/*) — NEVER src/ or implementation files.

3. **Validation:** Full suite (developer + QA additions) is validated. If QA's own
   tests expose failures → FAIL. Verdict includes `qa_review_notes` and `qa_tests_added`.

## Requirements

1. `agents/qa-manager.md` gains a new **checklist step 2a — Test Review &
   Augmentation** inserted between step 2 (Tests green) and step 2b (Tooling gates),
   with the following rules:
   - QA reads the story's `## Test criteria` section as the spec.
   - QA reads the developer's test file(s) on the feature branch.
   - QA derives test strategy from repo context: `qa_config.json` checkers,
     `process.json` `test_strategy` field, and existing test file patterns
     (file extensions, test runner imports, directory structure).
   - QA decides (judgment call — not mandatory): augment if developer tests have
     gaps, wrong assumptions, or missing edge cases from the spec.
   - If augmenting: write tests using the project's conventions; commit to the
     feature branch as `test(qa): augment coverage for <story-id>`.
   - Scope constraint (hard rule): QA writes ONLY to test files (tests/*, spec/*,
     e2e/*, playwright/*, __tests__/*). Writing to src/, lib/, app/, or any
     implementation file is FORBIDDEN in this phase.
   - If NOT augmenting: note "coverage sufficient" or "deliberate non-augmentation:
     <reason>" in `qa_review_notes`.
   - Provenance: `tier-k` (LLM judgment — no Tier D equivalent exists for test quality).
2. Verdict schema extended with two optional fields:
   - `qa_tests_added`: list of test function names added by QA (empty list if none).
   - `qa_review_notes`: string — brief note on test review findings (e.g. "added 2
     edge-case tests for empty input; developer tests covered happy path only").
3. `docs/features/_story_template.md` `## Test criteria` section gains a one-line note:
   "QA may augment or correct these criteria during the QA phase."
4. The update is consistent with the existing Tier D / Tier K split: test augmentation
   is explicitly Tier K (no script verifies test quality).

## Developer Targets (exactly, no more / no less)

- `agents/qa-manager.md`:
  - Insert new checklist step **2a — Test Review & Augmentation** between steps 2
    and 2b (requirements 1 + 4).
  - Extend the verdict schema JSON example at L14 to include `qa_tests_added` and
    `qa_review_notes` (requirement 2).
  - Update the step 2 header line to reference step 2a as the prerequisite
    (logical ordering: review before running).
  - Update module description line (L6) to mention the test oracle role.
- `docs/features/_story_template.md`:
  - Add one-line note to `## Test criteria` section (requirement 3).
- `tests/test_qa_manager_prompt.py`:
  - `test_qa_manager_has_test_review_step` — `qa-manager.md` contains "Test Review"
    (case-insensitive) in a checklist step.
  - `test_qa_manager_augmentation_scope_test_files_only` — `qa-manager.md` explicitly
    states QA writes ONLY to test files (contains "src/" in a prohibition/scope context,
    or equivalent phrasing about implementation files being forbidden).
  - `test_qa_manager_strategy_derived_from_repo_context` — `qa-manager.md` mentions
    deriving test strategy from `qa_config.json` or `process.json`.
  - `test_qa_manager_verdict_schema_has_qa_fields` — `qa-manager.md` verdict JSON
    contains `qa_tests_added` and `qa_review_notes`.
  - `test_story_template_has_qa_augmentation_note` — `_story_template.md`
    `## Test criteria` section contains "QA may augment".

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `qa-manager.md` contains a "Test Review & Augmentation" checklist step.
- `qa-manager.md` explicitly restricts QA test writing to test files (not src/).
- `qa-manager.md` references repo-context strategy derivation (qa_config.json /
  process.json / existing patterns).
- `qa-manager.md` verdict schema includes `qa_tests_added` and `qa_review_notes`.
- `_story_template.md` Test Criteria section notes QA augmentation.
- All 5 new tests pass; existing `test_qa_manager_has_tooling_gates_checklist_item` unaffected.
- No concrete model/provider names introduced.

## Test criteria (must exist BEFORE implementation)

QA may augment or correct these criteria during the QA phase.

- `test_qa_manager_has_test_review_step` — qa-manager.md contains "test review"
  (case-insensitive).
- `test_qa_manager_augmentation_scope_test_files_only` — qa-manager.md contains
  an explicit prohibition on writing to implementation files (src/ or equivalent).
- `test_qa_manager_strategy_derived_from_repo_context` — qa-manager.md mentions
  `qa_config.json` or `process.json` in the context of test strategy.
- `test_qa_manager_verdict_schema_has_qa_fields` — qa-manager.md verdict JSON
  contains `qa_tests_added` and `qa_review_notes`.
- `test_story_template_has_qa_augmentation_note` — `_story_template.md`
  contains "QA may augment".

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean — n/a (Markdown + test file changes only; no new Python module)
- [ ] Typecheck clean — n/a
- [ ] Format check clean (black — for test_qa_manager_prompt.py)
- [ ] Audit clean — n/a
