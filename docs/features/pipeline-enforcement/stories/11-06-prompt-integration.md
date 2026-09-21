# Story 11-06 — Prompt Integration and Documentation

Status: Done
Feature: pipeline-enforcement (F-007)

## Context / Purpose

The enforcement plugin complements the existing prompt rules — it doesn't replace them.
This story updates the agent prompts and AGENTS.md to reference the plugin guards, so the
LLM knows the guards exist and can give better error messages when a guard blocks an action.
It also documents the plugin in the README and updates the deployment procedure.

## Requirements

- `agent/architect.md` updated: mention that code edits are enforced by plugin (not just
  prompt rule), and that housekeeping-story flow exists for small fixes.
- `AGENTS.md` updated: add plugin to "Architecture" section, document guard list and
  deployment path.
- `README.md` updated: add plugin to the feature list and deployment procedure.
- Existing prompt rules stay intact (behavioral training) — plugin references are additive.

## Developer Targets (exactly, no more / no less)

- Update `agent/architect.md`:
  - Add note in the "no code" rule section: "This rule is enforced by the pipeline-enforcement
    plugin. If you attempt to edit code files, the plugin will block the action and ask the
    user to choose: housekeeping fix or full pipeline."
- Update `AGENTS.md`:
  - Add to "Architecture" section: `plugins/pipeline-enforcement.ts` description, guard list
    (merge, dev-start, architect-code, story-status), deployment path
- Update `README.md`:
  - Add "Pipeline Enforcement Plugin" to feature list
  - Add deployment note: plugin deploys with release branch like all other files
- Create `tests/test_prompt_integration.py`:
  - Test that `agent/architect.md` mentions "pipeline-enforcement" or "enforcement plugin"
  - Test that `AGENTS.md` mentions "plugins/pipeline-enforcement"
  - Test that `README.md` mentions "enforcement" or "plugin"

## Acceptance criteria (checked by qa-manager)

- `agent/architect.md` references the enforcement plugin
- `AGENTS.md` documents the plugin architecture and guard list
- `README.md` mentions the plugin
- Existing prompt rules are not removed (only augmented)
- All tests pass

## Test criteria (must exist BEFORE implementation)

- `tests/test_prompt_integration.py::test_architect_prompt_mentions_plugin` — agent/architect.md contains "enforcement" reference
- `tests/test_prompt_integration.py::test_agents_md_documents_plugin` — AGENTS.md contains "plugins/pipeline-enforcement"
- `tests/test_prompt_integration.py::test_readme_mentions_plugin` — README.md contains "enforcement" or "plugin"
