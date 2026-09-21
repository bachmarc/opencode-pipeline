# Story 13-06 — Migration Validation Script

Status: Planned
Feature: project-migration (F-009)

## Context / Purpose

After all migration steps, the Architect needs a deterministic check that everything is correct. This script validates the migrated project against pipeline expectations.

## Requirements

- Script `scripts/validate_migration.py` runs 8 validation checks
- Checks: AGENTS.md exists, template constancy, required dirs, qa_config, FEATURES.md, STORIES.md, pipeline intent, git initialized
- JSON output with per-check results and overall status

## Developer Targets (exactly, no more / no less)

- `scripts/validate_migration.py` — new script with `validate_migration(target_path: str) -> dict`
- `tests/test_validate_migration.py` — tests for each check passing and failing

## Acceptance criteria (checked by qa-manager)

- All 8 checks implemented, JSON output correct, exit codes proper, all tests pass

## Test criteria (must exist BEFORE implementation)

- Tests for fully valid project, missing individual files, invalid qa_config, template constancy pass/fail
