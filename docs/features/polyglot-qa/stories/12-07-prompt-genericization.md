# Story 12-07 — Genericize portable prompts: no runner names

Status: Planned
Feature: polyglot-qa (F-008)

## Context / Purpose

Portable agent/command prompts hard-name pytest: qa-manager.md ("compressed
pytest list", "Check via pytest"), developer.md ("Run: pytest, ruff, mypy",
"`pytest` must be green"), architect.md ("Do NOT run pytest yourself"),
command/implement.md, qa-check.md, qa_summary.md, status.md. This leaks a
project-level decision into framework files — the same discipline violation
as the model de-hardwiring (RETRO-02). The prompts must reference "the
project's configured test suite" instead. Pinned self-tests
(test_orchestration_rules.py etc.) must move first (tests-first) so the
invariant "no runner names in portable prompts" is enforceable.

## Requirements

- Portable prompts reference the **configured test suite** /
`qa_config.json`, never a concrete runner name:
  - `agent/qa-manager.md`: "compressed pytest list" → "compressed test
    summary"; "Check via `pytest`" → "Check via the project's configured
    checkers (`qa_config.json`) / `qa_compress.sh`".
  - `agent/developer.md`: "Run: `pytest`, `ruff`, `mypy`" → "Run the
    project's configured test suite via `scripts/qa_compress.sh`" (plus
    project-specific linters if configured); "`pytest` green" → "configured
    test suite green".
  - `agent/architect.md`: "Do NOT run pytest yourself" → "Do NOT run the
    test suite yourself" (same rule, runner-agnostic wording); merge-conflict
    exception likewise generic; BLOCKED_Design lean-context note "No pytest
    log" → "No raw test logs".
  - `command/implement.md`: "Check `pytest` green" → "Check the configured
    test suite green (qa_compress.sh)".
  - `command/qa-check.md`, `command/qa_summary.md`, `command/status.md`:
    pytest mentions → "test suite" / "configured checkers".
- The semantic rules stay EXACTLY the same — only wording becomes
  runner-agnostic. No behavior change.
- Self-tests pin the new invariant (tests-first): a framework test asserts
  that `agent/*.md` and `command/*.md` contain no runner names from the
  forbidden list (`pytest`, `rspec`, `jest`, `gradle`, `maven`) — with a
  documented allowlist where the framework REQUIRES naming a runner (e.g.
  qa_compress.sh docs, requirements.txt pin — NOT portable prompts).
- Frontmatter descriptions update accordingly (qa-manager.md line 2
  "compressed pytest list" etc.).

## Developer Targets (exactly, no more / no less)

- New test file `tests/test_no_runner_names_in_prompts.py` FIRST (red against
  current prompts), then:
- Edit `agent/qa-manager.md` (frontmatter description + checklist point 2 +
  rules point on pytest): genericize as specified.
- Edit `agent/developer.md` (steps 7, 26/48 line refs in story): genericize.
- Edit `agent/architect.md` (Phase 3 Orchestration + Merge Discipline +
  Autonomous Design Repair): genericize, keeping "Do NOT run the test suite
  yourself" rule recognizable.
- Edit `command/implement.md`, `command/qa-check.md`, `command/qa_summary.md`,
  `command/status.md`: genericize.
- Update `tests/test_orchestration_rules.py::test_architect_no_own_pytest_rule`
  → `test_architect_no_own_testsuite_run_rule`: asserts
  `"Do NOT run the test suite yourself"` in architect.md (old string no
  longer pinned).
- Update `tests/test_readme_structure.py` ONLY IF it pins pytest strings in
  agent files (verify, don't guess).
- No changes to `qa_compress.sh`, plugin checkers, or any script logic —
  prompt text only.

## Acceptance criteria (checked by qa-manager)

- `tests/test_no_runner_names_in_prompts.py` green: no runner name from the
  forbidden list in any `agent/*.md` or `command/*.md` (with allowlist entries
  documented in the test itself).
- All existing framework self-checks green (test_framework, test_qa_scripts,
  test_orchestration_rules with the updated rule name).
- Prompts still describe the SAME rules (single-story enforcement, no
  architect test runs, compressed summaries) — semantics unchanged, only
  runner-agnostic wording.
- No model/provider names introduced (existing check stays green).

## Test criteria (must exist BEFORE implementation)

`tests/test_no_runner_names_in_prompts.py`:

- `test_no_runner_names_in_agent_prompts` — for every `agent/*.md`: no
  occurrence of `pytest`, `rspec`, `jest`, `gradle`, `maven` (case-insensitive).
- `test_no_runner_names_in_command_prompts` — same for every `command/*.md`.
- `test_generic_testsuite_wording_present` — architect.md contains
  "Do NOT run the test suite yourself"; qa-manager.md contains "configured
  test suite" or "configured checkers"; developer.md contains "configured
  test suite".