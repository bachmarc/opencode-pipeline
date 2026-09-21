# Story 13-01 — /migrate-project Command + migrate-project Skill Scaffold

Status: Planned
Feature: project-migration (F-009)

## Context / Purpose

The pipeline currently has no mechanism to onboard existing projects. The `/new-project` command only works for greenfield projects (it exits if `AGENTS.md` already exists). Existing projects need an interactive migration path that understands their current state and guides the user through onboarding.

This story creates the entry point: a `/migrate-project` command that triggers the Architect, and a `migrate-project` skill that the Architect loads to guide the migration dialogue.

## Requirements

- A `/migrate-project` command exists that triggers the Architect agent
- A `skills/migrate-project.md` skill exists with the migration workflow instructions
- The command accepts an optional path argument (defaults to current project directory)
- The skill defines the migration phases: analyze → dialogue → generate AGENTS.md → provision structure → optional retro stories → validate

## Developer Targets (exactly, no more / no less)

- `command/migrate-project.md` — new command file with `agent: architect`
- `skills/migrate-project.md` — new skill file defining the 6-phase migration workflow
- `tests/test_migrate_command.py` — verify command file exists, has correct frontmatter
- `tests/test_migrate_skill.py` — verify skill file exists, contains all 6 phase references and script names

## Acceptance criteria (checked by qa-manager)

- `command/migrate-project.md` exists with correct frontmatter (`agent: architect`)
- `skills/migrate-project.md` exists and references all 6 migration phases
- The skill references the expected script names
- No Python application code — only markdown files plus test files

## Test criteria (must exist BEFORE implementation)

- `tests/test_migrate_command.py` — verify command file exists, has correct frontmatter
- `tests/test_migrate_skill.py` — verify skill file exists, contains all 6 phase references and script names
