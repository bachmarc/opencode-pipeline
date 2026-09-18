# Story 12-09 — Template migration tool for existing projects

Status: Planned
Feature: polyglot-qa (F-008)

## Context / Purpose

The 12-08 template change (runner-agnostic constant sections) makes existing
project AGENTS.md files fail `check_template_constancy.py` until their
constant sections are re-synced once. The architect must be able to migrate
existing projects (netclip, vokabel, intesis_modbus reference projects, any
scaffolded project) with ONE deterministic command instead of hand-editing
markdown. The user asked for exactly this ("der architect soll migrieren
können") after initially not seeing the problem — resolved: the constancy
check compares template vs. project; a template change invalidates all
existing copies; the migration tool re-syncs them without destroying
project-specific content.

## Requirements

- New script `scripts/migrate_template_sections.py <project-agents-md>`:
  - Replaces ONLY the constant sections (Workflow, Git conventions,
    Languages, Prohibitions) in the given project AGENTS.md with the current
    `templates/AGENTS.md` sections.
  - Preserves everything outside those sections byte-identical (project
    name, stack, core rules, architecture, references).
  - Section detection: exact heading match (`## Workflow`, `## Git
    conventions`, `## Languages`, `## Prohibitions`) up to the next `## `
    heading — same extraction logic as `check_template_constancy.py`
    (shared logic may be imported or duplicated; duplication acceptable for
    a one-time migration tool).
  - Idempotent: migrating an already-migrated file changes nothing (exit 0).
  - Missing file → exit 1 with JSON error. File with no recognizable constant
    sections (e.g. plain markdown) → exit 1, JSON error `no constant
    sections found`, file untouched.
  - Output: JSON `{"migrated": true, "sections": [...]}` / idempotent:
    `{"migrated": false, "reason": "already current"}`.
- Missing-section handling: if the project file lacks one of the four
    constant sections entirely, the tool INSERTS it before `## References`
    (or at EOF if absent) — old templates always contained all four, so this
    is a safety path, tested but not expected in practice.
- Architect onboarding duty documented (no code): architect prompt already
  genericized in 12-07; this story adds to `docs/requirements.md`
  Polyglot-QA section a one-paragraph runbook: "When adopting this pipeline
  version in an existing project: run migrate_template_sections.py once,
  then verify with check_template_constancy.py, then adapt qa_config.json
  to the project stack."

## Developer Targets (exactly, no more / no less)

- New `scripts/migrate_template_sections.py` with the behavior above
  (exit codes: 0 migrated-or-idempotent, 1 error).
- `tests/test_migrate_template_sections.py` (see test criteria).

## Acceptance criteria (checked by qa-manager)

- Project AGENTS.md with OLD constant sections (pre-12-08 wording, e.g.
  `pytest` in Workflow §3) + project-specific content around them →
  migration replaces the four constant sections with the new template
  sections; project-specific sections untouched (byte-identical).
- Running `check_template_constancy.py` on the migrated file → PASS.
- Idempotent second run → `{"migrated": false, "reason": "already current"}`,
  file unchanged, exit 0.
- Missing input file → exit 1, JSON error. No constant sections → exit 1,
  file untouched.
- Existing self-checks green; no model/provider names.

## Test criteria (must exist BEFORE implementation)

`tests/test_migrate_template_sections.py` — tmp_path:

- `test_migrate_old_project_agents` — write project AGENTS.md = new
  template with the two constant-section lines REVERTED to old wording
  (`pytest` lines back in) + a custom "## This project" section; run tool →
  `check_template_constancy.py` PASSes the file, custom section
  byte-identical, `"migrated": true` in output.
- `test_migrate_idempotent` — run twice → second run returns
  `"migrated": false`, "already current", file mtime/content unchanged.
- `test_migrate_missing_file` — nonexistent path → exit 1, JSON contains
  `error`.
- `test_migrate_no_sections` — file without any constant section headings →
  exit 1, `no constant sections found`, file unchanged on disk.
- `test_migrate_inserts_missing_section` — file with only Workflow + Git
  sections (Languages/Prohibitions removed) → tool inserts both before
  `## References`, constancy check PASSes afterwards.