# Story 15-01 — Code Documentation Rule in Story Template

Status: Planned
Feature: living-code-docs (F-011)

## Context / Purpose

Currently, stories define Developer Targets (file-by-file changes) and Test Criteria, but
there is no rule requiring developers to update docstrings and module headers in the files
they change. This means code-level documentation drifts silently — functions get new
parameters, modules gain new responsibilities, but the comments and docstrings still
describe the old behavior.

By adding a code documentation requirement to the story template and the developer prompt,
every story automatically carries the obligation to keep docstrings/headers current in
changed files. The code itself becomes the authoritative source of truth at the
function/module level.

## Requirements

1. The story template (`docs/features/_story_template.md`) must include guidance that
   developer targets include updating docstrings/headers in changed files.
2. The developer agent prompt (`agent/developer.md`) must include a rule that changed
   files must have current docstrings/module headers.
3. The architect agent prompt (`agent/architect.md`) must include guidance to consider
   code documentation when writing Developer Targets sections.
4. A test must verify the story template contains the code-doc guidance.

## Developer Targets (exactly, no more / no less)

- `docs/features/_story_template.md`: Add a note under "## Developer Targets" that
  changed files must have updated docstrings/module headers. Keep it brief — one line
  of guidance, not a paragraph.
- `agent/developer.md`: Add a rule in the Rules section: "Update docstrings and module
  headers in every file you change. Code documentation is the source of truth."
- `agent/architect.md`: Add guidance that Developer Targets should include docstring
  updates when a file's purpose or interface changes.
- `tests/test_templates.py`: Add test `test_story_template_has_code_doc_guidance` that
  verifies the story template contains docstring/header update guidance.
- `tests/test_framework.py`: Add test `test_developer_prompt_has_code_doc_rule` that
  verifies agent/developer.md contains the code documentation rule.

## Acceptance criteria (checked by qa-manager)

- Story template contains code-doc guidance in the Developer Targets section
- Developer prompt contains code documentation rule
- Architect prompt contains code-doc guidance for story writing
- New tests pass and existing tests remain green
- No model/provider names introduced in any changed file

## Test criteria (must exist BEFORE implementation)

- `tests/test_templates.py::test_story_template_has_code_doc_guidance` — asserts
  "docstring" or "module header" appears in the Developer Targets section of the template
- `tests/test_framework.py::test_developer_prompt_has_code_doc_rule` — asserts
  agent/developer.md contains "docstring" and "source of truth" in a rules context
