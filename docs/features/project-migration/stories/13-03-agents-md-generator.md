# Story 13-03 — AGENTS.md Generator (LLM-Assisted via Skill Dialogue)

Status: Planned
Feature: project-migration (F-009)

## Context / Purpose

This script prepares a draft AGENTS.md by combining the template's constant sections with project-specific data from the analysis JSON. The Architect then uses this draft for interactive dialogue with the user.

## Requirements

- Script `scripts/prepare_agents_md.py` takes analysis JSON and produces a draft AGENTS.md
- Constant sections copied verbatim from template, project-specific sections pre-populated where possible
- `<TODO>` markers for undetermined fields, existing agent file content as comment block

## Developer Targets (exactly, no more / no less)

- `scripts/prepare_agents_md.py` — new script with `prepare_agents_md(analysis: dict, template_path: str) -> str`
- `tests/test_prepare_agents_md.py` — tests for constant sections, project name, stack, TODO markers

## Acceptance criteria (checked by qa-manager)

- Constant sections byte-identical to template, project data extracted, TODO markers present, all tests pass

## Test criteria (must exist BEFORE implementation)

- Tests for constant section matching, project name extraction, stack line, TODO markers, existing content preservation
