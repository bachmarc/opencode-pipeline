# Story 13-04 — Structure Provisioning Script

Status: Done (172537a)
Feature: project-migration (F-009)

## Context / Purpose

After AGENTS.md is generated, the project needs pipeline directory structure and config files. This script creates only what's missing, never overwrites existing files.

## Requirements

- Script `scripts/provision_structure.py` creates missing directories and files
- Stack-aware `qa_config.json`, template copying, `.gitignore` merge logic
- Never overwrites existing files

## Developer Targets (exactly, no more / no less)

- `scripts/provision_structure.py` — new script with `provision_structure(target_path: str, analysis: dict) -> dict`
- `tests/test_provision_structure.py` — tests for directory creation, qa_config, gitignore merge, no-overwrite

## Acceptance criteria (checked by qa-manager)

- Creates only missing items, correct qa_config per stack, gitignore merge works, all tests pass

## Test criteria (must exist BEFORE implementation)

- Tests for missing dir creation, existing dir skip, qa_config per stack, no-overwrite, gitignore merge
