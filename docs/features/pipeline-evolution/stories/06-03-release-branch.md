# Story 06-03 — Release branch setup

Status: Done
Feature: pipeline-evolution (F-004)

## Context / Purpose

Establish the `release` branch strategy: `main` = development line, `release` = stable
deployable state. Includes documentation update and a convenience script for promotion.

## Requirements

After this story, a `release` branch exists, the README documents the new strategy, and
a script handles the `main` → `release` promotion.

## Developer Targets (exactly, no more / no less)

- Create `release` branch from current `main` HEAD
- Create `scripts/promote_release.py`:
  - Validates that `main` is clean and up-to-date with remote
  - Fast-forward merges `release` to current `main` HEAD
  - Pushes `release` to remote
  - Outputs JSON: `{"promoted": true, "from": "<commit>", "to": "<commit>"}`
  - Exit code 0 on success, 1 on dirty state / behind remote
- Update README.md § Deployment: Live clone pulls `release`, not `main`
- Update AGENTS.md: reflect `release` branch in deployment rules

## Acceptance criteria (checked by qa-manager)

- `release` branch exists on remote
- `scripts/promote_release.py` works and handles error cases
- README documents the new branching strategy
- AGENTS.md references `release` for deployment

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_promote_release.py::test_script_exists` — `scripts/promote_release.py` exists and is valid Python (`py_compile`)
- `tests/test_promote_release.py::test_script_has_main_guard` — script has `if __name__ == "__main__"` entry point
- `tests/test_promote_release.py::test_readme_mentions_release_branch` — README contains "release" branch documentation
- `tests/test_promote_release.py::test_agents_md_mentions_release` — AGENTS.md references `release` for deployment
