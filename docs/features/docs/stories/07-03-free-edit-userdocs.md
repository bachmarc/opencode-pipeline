# Story 07-03 — Free Edit Userdocs

Status: Planned
Feature: docs (F-003)

## Context / Purpose

User-facing documentation (`README.md` and similar end-user docs) currently carries
enforceable prose tests in several test files. Because this repo treats "testable files"
as the trigger for story + QA-gate, every README edit (no matter how trivial) is forced
through a story with test criteria — pure overhead. The repo's own `test_framework.py`
(Phase 01) is the only check that actually scans portable role files; it never scanned
`README.md`. The `test_readme_structure.py`, `test_deploy_docs.py`,
`test_prompt_integration.py`, and `test_promote_release.py` suites are what make README
content "testable" and thereby story-mandatory.

Goal: end-user docs become **free-edit** — directly editable on-the-fly by `build` and
`architect` (and any agent), without a story, without test criteria, without formal
procedure. Internal/derived data (code, methods, architect data, `docs/requirements.md`,
`docs/design.md`, feature/story infrastructure) stays governed — but no story overhead for
routine doc touches. Removing the prose tests is the mechanism that lifts the story burden.

## Requirements

- `README.md` and similar user-facing docs are **free-edit**: any agent (build, architect)
  can edit them directly, on the fly, without creating a story or test criteria.
- No prose/content/structure asserts on README content remain in the test suite — a README
  edit no longer triggers a testable-file/QA-stories cycle.
- Internal/derived docs (`docs/requirements.md`, `docs/design.md`) and feature/story
  infrastructure remain governed by the existing Documenter/Architect flow.
- `agent/documenter.md` stays `mode: subagent` (unchanged) — the Documenter-guard plugin
  and `test_documenter*.py` are **untouched**.
- `test_framework.py` (portable role abstraction: no model names in `agent/`,
  `command/`, `skills/`, `templates/`, `scripts/`) is **unchanged** — it never scanned
  `README.md` and stays as the real invariant.
- The free-edit rule is documented so future sessions know end-user docs need no story.

## Developer Targets (exactly, no more / no less)

- **`tests/test_readme_structure.py`** — delete the file entirely (it only asserts README
  prose/structure: section order, mermaid, anchors, agent intro, reasoning-effort,
  no-model-names). Removed from the test area.
- **`tests/test_deploy_docs.py`** — remove `test_readme_deployment_section` (the only
  function in the file, asserts README Deployment-section prose). If the file becomes empty
  as a result, delete the file.
- **`tests/test_prompt_integration.py`** — remove only `test_readme_mentions_plugin`.
  Keep `test_architect_prompt_mentions_plugin` and `test_agents_md_documents_plugin`
  (they check agent files, part of the governed/tested area).
- **`tests/test_promote_release.py`** — remove only `test_readme_mentions_release_branch`.
  Keep `test_script_exists`, `test_script_has_main_guard`, `test_agents_md_mentions_release`.
- **Documentation of the free-edit rule** — add a short note so the rule is visible:
  in `docs/design.md` "README Structure" section, state that `README.md` and user-facing
  docs are a **free-edit** area (no story/test criteria; editable by build/architect /
  any agent), while internal/derived docs stay governed. Keep it concise.
- **Do NOT modify:** `tests/test_framework.py`, `agent/documenter.md`, the
  documenter-guard plugin (`plugins/guards/documenter-guard.ts`), `tests/test_documenter*.py`,
  `docs/requirements.md`, `docs/design.md` internals beyond the one free-edit note, or any
  feature/story file other than this story and its feature index.

## Acceptance criteria (checked by qa-manager)

- `tests/test_readme_structure.py` is gone.
- `test_deploy_docs.py` (if still a file) contains no README assertion; if it had only that
  one, the file is gone.
- `test_prompt_integration.py` and `test_promote_release.py` still pass and no longer
  contain a README-content assertion (their non-README checks remain intact).
- `pytest tests/` is fully green.
- `agent/documenter.md` mode is still `subagent`; documenter-guard still present;
  `test_documenter*.py` unchanged and green.
- `test_framework.py` unchanged; its no-model-names check for portable role files still
  passes.
- `docs/design.md` contains the free-edit note for end-user docs vs. governed internal docs.
- The free-edit rule is visible to future sessions (via the design.md note and this story).

## Test criteria (must exist BEFORE implementation)

These are **removal/relocation** tests — they pin the intended end state so QA verifies the
free-edit scope deterministically. New/extended tests in this story's feature branch:

- `tests/test_free_edit.py` (new) — asserts the free-edit rule is documented in
  `docs/design.md` ("free-edit" and the user-facing-vs-governed split are mentioned) and
  that no prose-content test references README text for structure/anchors/deployment/
  plugin/release-branch content anymore (i.e. the README-content test functions named
  above no longer exist in `tests/`).
- Existing `tests/test_framework.py` must stay green (untouched).
- Existing `tests/test_documenter.py`, `tests/test_documenter_prompt.py`,
  `tests/test_documenter_guard.py` must stay green (untouched).
- The removal itself is deterministic (file/function presence asserts) and must run green
  only AFTER the README-content tests are removed and the design.md note is added.
