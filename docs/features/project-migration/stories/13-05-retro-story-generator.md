# Story 13-05 — Retro Story Generator Script

Status: Planned
Feature: project-migration (F-009)

## Context / Purpose

When migrating an existing project, the user may want to document pre-pipeline development as retro stories. This script creates retro story files and feature directory from a JSON definition.

## Requirements

- Script `scripts/create_retro_stories.py` takes project path and retro definition JSON
- Creates feature directory, feature.md, story files with "Retro-Done" status
- Appends to FEATURES.md and STORIES.md, never overwrites existing retro files

## Developer Targets (exactly, no more / no less)

- `scripts/create_retro_stories.py` — new script with `create_retro_stories(target_path: str, retro_def: dict) -> dict`
- `tests/test_create_retro_stories.py` — tests for feature/story creation, index updates, no-overwrite

## Acceptance criteria (checked by qa-manager)

- Feature.md follows template, story files have "Retro-Done" status, indexes updated, all tests pass

## Test criteria (must exist BEFORE implementation)

- Tests for feature dir creation, single/multiple stories, index updates, no-overwrite
