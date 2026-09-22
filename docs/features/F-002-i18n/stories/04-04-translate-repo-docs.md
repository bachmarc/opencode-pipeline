# Story 04-04 — Translate AGENTS.md + STORIES.md to English

Status: Done
Feature: i18n (F-002)

## Context / Purpose

The repo-root `AGENTS.md` (project-specific guardrails) and `STORIES.md` (story index)
still contain German prose, status labels, and phase comments. They must be translated
to English for consistency with the rest of the repo.

Note: `AGENTS.md` at repo root is project-specific (not the template). It was already
partially English but contains German fragments. `STORIES.md` has German status labels
and phase comments.

## Requirements

After this story, both files are fully English. Status labels use English terms
(`Done`, `Planned`, `In Progress`). Phase comments are English. The `AGENTS.md`
Languages section reflects the new policy: "Respond in the user's language."

## Developer Targets (exactly, no more / no less)

- **`AGENTS.md` (repo root)**: Translate all remaining German prose to English.
  Specifically:
  - Section "Languages": replace hardcoded "Dialogue with user: German" / "UI-Texte:
    Deutsch" with "Dialogue with user: respond in the user's language" / "UI text:
    per project configuration"
  - Any remaining German phrases in other sections
  - Technical identifiers, file paths, code blocks unchanged
- **`STORIES.md`**: Already updated by architect (phase comments + status labels are
  English). Developer verifies no German fragments remain and fixes any found.

## Acceptance criteria (checked by qa-manager)

- Zero German prose in `AGENTS.md` (repo root) and `STORIES.md`.
- `AGENTS.md` Languages section no longer hardcodes "German" as dialogue language.
- All file paths, code blocks, technical identifiers unchanged.
- No test file changes needed — these files are not scanned by `test_framework.py`
  portable-file checks (they are in the repo root, not in `agent/`/`command/`/etc.).

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- Manual review: grep for common German words (`Deutsch`, `Erledigt`, `Geplant`,
  `Phasen-Kommentar`, `Reine`, `Doku`) in `AGENTS.md` and `STORIES.md` — must return
  zero hits.
- `pytest tests/` full suite passes (no regressions).
