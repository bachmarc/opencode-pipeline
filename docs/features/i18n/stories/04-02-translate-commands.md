# Story 04-02 — Translate command/*.md to English

Status: Done
Feature: i18n (F-002)

## Context / Purpose

All seven command files in `command/` have German descriptions and instruction bodies.
They must be translated to English for international accessibility.

## Requirements

After this story, all command files are English. Frontmatter `description` fields and
instruction bodies are translated. Technical identifiers, file paths, variable references
(`$ARGUMENTS`), and code examples remain unchanged.

## Developer Targets (exactly, no more / no less)

- **`command/decompose.md`**: Translate `description` + body to English.
- **`command/implement.md`**: Translate `description` + body to English.
- **`command/new-project.md`**: Translate `description` + body to English.
- **`command/qa_summary.md`**: Translate `description` + body to English.
- **`command/qa-check.md`**: Translate `description` + body to English.
- **`command/requirements.md`**: Translate `description` + body to English.
- **`command/status.md`**: Translate `description` + body to English.

Preservation rules for all files:
- All file paths, `$ARGUMENTS` references, code blocks, and technical terms unchanged.
- Frontmatter keys (`description`, `agent`) and their structure unchanged.

## Acceptance criteria (checked by qa-manager)

- All seven files contain zero German prose.
- Frontmatter is valid and unchanged in structure.
- All file paths, `$ARGUMENTS`, code blocks unchanged.
- `pytest tests/test_framework.py::test_no_model_names_in_portable_files` passes.

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `pytest tests/test_framework.py::test_no_model_names_in_portable_files` — validates
  no model names leaked during translation.
- Manual review: grep for common German words (`Dekomponiere`, `Implementiere`, `Lege`,
  `Führe`, `Prüfe`, `Zeige`, `Starte`) in `command/*.md` — must return zero hits.
