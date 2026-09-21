# Story 06-10 — Documenter agent and /document command

Status: Done
Feature: pipeline-evolution (F-004)

## Context / Purpose

Create the Documenter agent role (cheap model) and the `/document` command. The Documenter
reconciles documentation against actual code state, triggered automatically after QA-PASS
or manually via command.

## Requirements

After this story, `agent/documenter.md` exists with the correct prompt, `command/document.md`
is available, and the QA-Manager prompt includes the auto-trigger instruction.

## Developer Targets (exactly, no more / no less)

- Create `agent/documenter.md`:
  - Frontmatter: `description`, `mode: subagent`, `temperature: 0.2`
  - Prompt body per Design §12: receive diff, check docs consistency, update README,
    design docs, docstrings, remove stale comments
  - Clear boundaries: does not make architecture decisions, does not write code,
    does not judge correctness, does not invent docs for unchanged code
- Create `command/document.md`:
  - Frontmatter: `description`, `agent: documenter`
  - Accepts `$ARGUMENTS` (feature-name, story-id, or empty for full check)
  - Instructions: run git diff against main, read affected files + docs, reconcile
- Update `agent/qa-manager.md`:
  - Add instruction: "On PASS verdict, before signaling merge-ready to Architect,
    spawn `documenter` with the feature branch diff as context"
- No model names in any file (model assigned via `opencode.jsonc`)

## Acceptance criteria (checked by qa-manager)

- `agent/documenter.md` exists with valid frontmatter (description, mode, temperature)
- `command/document.md` exists with valid frontmatter (description, agent)
- `agent/qa-manager.md` references documenter spawn after PASS
- No concrete model/provider names in any of the files
- Documenter prompt clearly states boundaries (what it does NOT do)

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_framework.py` existing checks pass (frontmatter validation, no model names)
  — the existing test_framework.py already scans `agent/*.md` for frontmatter and model
  names, so adding `documenter.md` automatically includes it
- `tests/test_documenter.py::test_documenter_frontmatter` — `agent/documenter.md` has required keys (description, mode, temperature)
- `tests/test_documenter.py::test_documenter_mode_subagent` — mode is `subagent`
- `tests/test_documenter.py::test_document_command_exists` — `command/document.md` exists with `agent: documenter`
- `tests/test_documenter.py::test_qa_manager_references_documenter` — `agent/qa-manager.md` contains "documenter"
- `tests/test_documenter.py::test_documenter_no_model_names` — no concrete model names in `agent/documenter.md`
