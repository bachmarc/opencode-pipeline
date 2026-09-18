# Story 04-01 — Translate agent/*.md to English

Status: Planned
Feature: i18n (F-002)

## Context / Purpose

All three agent prompt files (`architect.md`, `developer.md`, `qa-manager.md`) are
currently written in German. They must be translated to English so the framework is
accessible to international team members. Dialogue language is decoupled — agents will
respond in the user's language as configured per project.

## Requirements

After this story, all agent prompts are English. The frontmatter `description` field,
all section headers, all prose, and all inline comments are in English. Technical
identifiers, file paths, code examples, and JSON structures remain unchanged.

## Developer Targets (exactly, no more / no less)

- **`agent/architect.md`**: Translate frontmatter `description` + full prompt body to
  English. Preserve all file paths, code blocks, JSON examples, and technical terms.
  Replace "Deutsch mit User" language rule with "Respond in the user's language"
  (configurable per project).
- **`agent/developer.md`**: Translate frontmatter `description` + full prompt body to
  English. Same preservation rules.
- **`agent/qa-manager.md`**: Translate frontmatter `description` + full prompt body to
  English. Same preservation rules.

## Acceptance criteria (checked by qa-manager)

- All three files contain zero German prose (no German sentences, section headers, or
  inline comments). Technical terms that happen to be German words in code references
  (e.g. `vokabel/STORIES.md`) are exempt.
- Frontmatter is valid: `description` (English), `mode`, `temperature` present; no
  `model:` key.
- All file paths, code blocks, JSON structures, and technical identifiers are unchanged.
- `pytest tests/test_framework.py` passes (frontmatter check + model-name check).

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `pytest tests/test_framework.py::test_agent_frontmatter` — validates frontmatter
  structure is intact after translation.
- `pytest tests/test_framework.py::test_no_model_names_in_portable_files` — validates
  no model names leaked during translation.
- Manual review: grep for common German words (`Dein`, `Aufgaben`, `Regeln`, `Pflicht`,
  `Ablauf`, `Ergebnis`) in `agent/*.md` — must return zero hits.
