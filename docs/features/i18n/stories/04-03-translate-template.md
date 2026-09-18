# Story 04-03 — Translate templates/AGENTS.md to English

Status: Planned
Feature: i18n (F-002)

## Context / Purpose

The project template `templates/AGENTS.md` contains German section headers, placeholder
descriptions, and prose. It must be translated to English. This is the skeleton that every
new project copies — it defines the binding interface between framework and project.

## Requirements

After this story, `templates/AGENTS.md` is fully English: section headers, placeholder
text inside `<...>`, prose descriptions, and comments. The constant sections (Workflow,
Git conventions, Languages, Prohibitions) use English headers. Placeholders remain as
`<...>` patterns for project-specific filling.

## Developer Targets (exactly, no more / no less)

- **`templates/AGENTS.md`**: Translate all content to English:
  - Section headers: `## Dieses Projekt` → `## This project`, `## Kernregeln` →
    `## Core rules`, `## Architektur: Funktion vs Konnektivität` →
    `## Architecture: function vs connectivity`, `## Git-Konvention` →
    `## Git conventions`, `## Sprachen` → `## Languages`, `## Verbote` →
    `## Prohibitions`, `## Referenzen` → `## References`
  - All placeholder descriptions inside `<...>` translated to English
  - All prose/bullet points translated to English
  - The intro comment block translated to English
  - Technical identifiers, file paths, code blocks, JSON unchanged
- **`docs/stories/_template.md`**: Translate the story template to English (headers
  and placeholder descriptions).

## Acceptance criteria (checked by qa-manager)

- Zero German prose in `templates/AGENTS.md` and `docs/stories/_template.md`.
- `templates/AGENTS.md` contains English constant section markers: `## Workflow`,
  `## Git conventions` (or `## Git`), `## Languages`, `## Prohibitions`.
- At least one `<...>` placeholder pattern still present.
- `pytest tests/test_framework.py::test_template_exists_and_const` passes.
- `pytest tests/test_framework.py::test_no_model_names_in_portable_files` passes.

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `pytest tests/test_framework.py::test_template_exists_and_const` — validates constant
  section markers (already accepts English alternatives) and placeholder presence.
- `pytest tests/test_framework.py::test_no_model_names_in_portable_files` — validates
  no model names leaked.
- Manual review: grep for German section headers (`Dieses Projekt`, `Kernregeln`,
  `Verbote`, `Sprachen`) in `templates/AGENTS.md` — must return zero hits.
