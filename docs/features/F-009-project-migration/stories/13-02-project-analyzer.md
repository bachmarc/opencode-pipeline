# Story 13-02 — Project Analyzer Script

Status: Done (172537a)
Feature: project-migration (F-009)

## Context / Purpose

Before the Architect can guide a migration dialogue, it needs a deterministic analysis of the target project. This script scans the project and produces a structured JSON report: stack, agent file, directory structure, git state.

## Requirements

- Script `scripts/analyze_project.py` accepts a project path and outputs JSON to stdout
- Stack detection, agent file detection, structure analysis, git analysis
- Exit code 0 on success, 1 if path doesn't exist, 2 if not a directory

## Developer Targets (exactly, no more / no less)

- `scripts/analyze_project.py` — new script with `analyze_project(target_path: str) -> dict`
- `tests/test_analyze_project.py` — tests for stack detection, agent file detection, structure analysis

## Acceptance criteria (checked by qa-manager)

- Script exists, output is valid JSON, stack detection works, no side effects, all tests pass

## Test criteria (must exist BEFORE implementation)

- Tests for Python/JS/Ruby/Java/mixed/unknown stack detection
- Tests for AGENTS.md/CLAUDE.md/none agent file detection
- Tests for missing/present directories, nonexistent path
