# Story <ID> — <Title>

Status: Planned | In Progress | Done
Feature: <feature-name> (<feature-id>)

## Context / Purpose

<Why does this story exist? What problem does it solve? Self-contained — no external references needed>

## Requirements

<What must be true when this story is done? Functional requirements in the story's own words>

**Guidance for architects:** If any requirement is ambiguous or not explicitly decided by the user, mark it with `[NEEDS CLARIFICATION: <specific question>]` instead of guessing. The user resolves these at the review checkpoint before implementation starts.

## Developer Targets (exactly, no more / no less)

- <Concrete changes — file by file>
- Update docstrings and module headers in every file you change — code documentation is the source of truth.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- <Deterministically verifiable criteria>

## Test criteria (must exist BEFORE implementation)

- <Tests written first — file, test name, expected behavior>
