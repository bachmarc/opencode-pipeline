# Story 12-12 — Dev-start-guard: strip story slug when parsing STORIES.md

Status: Planned
Feature: polyglot-qa (F-008) — pipeline-enforcement bugfix, discovered during
Phase 12 orchestration

## Context / Purpose

The dev-start-guard warns `Unknown story ID: 12-01 (not found in STORIES.md)`
for every legitimate story spawn. Cause: the guard extracts the bare story ID
(`12-01`) from the spawn prompt, but when parsing the STORIES.md table it reads
`parts[1]` — which is the full row ID **with slug** (`12-01-qa-config-contract`).
The subsequent pattern test `^(\d{2}-\d{2}|RETRO-\d{2})$` never matches a
slugged row, so the status map stays empty and every known story ID is
reported as unknown. The guard is advisory (nothing was blocked), but the
warning is wrong and hides real signals.

## Requirements

- STORIES.md row parsing in `plugins/guards/dev-start-guard.ts` normalizes
  the row ID before the pattern test: strip the slug suffix so
  `12-01-qa-config-contract` → `12-01` and `RETRO-01` → `RETRO-01`
  (first two dash-separated segments joined by `-`).
- Pattern test, status extraction (`parts[3]`), and all warning semantics
  unchanged otherwise.
- The guard remains advisory (warnings, no throw).

## Developer Targets (exactly, no more / no less)

- `plugins/guards/dev-start-guard.ts`: in the table-parsing loop, normalize
  `parts[1]` via its first two dash segments before the
  `/^(\d{2}-\d{2}|RETRO-\d{2})$/` test (e.g.
  `const storyId = parts[1].split("-").slice(0, 2).join("-")`). Keep the
  existing pattern test and map insertion semantics; do not touch any other
  guard.
- `tests/test_dev_start_guard.py`: add
  `test_dev_start_guard_strips_slug` (see test criteria).

## Acceptance criteria (checked by qa-manager)

- `pytest tests/test_dev_start_guard.py` fully green (existing 4 tests +
  new one).
- Full suite green.
- Guard change limited to the normalization; no other guards or plugin
  files touched.

## Test criteria (must exist BEFORE implementation)

`tests/test_dev_start_guard.py` — string-based assertion, consistent with
the repo's existing plugin-test style:

- `test_dev_start_guard_strips_slug` — red first: asserts that
  `dev-start-guard.ts` contains slug normalization (`.split("-")` AND
  `.slice(0, 2)` in the file); currently absent → red. After fix → green.
- Additionally `test_dev_start_guard_stories_rows_with_slugs` — reads the
  repo's own STORIES.md, applies the same normalization in Python
  (`line.split("|")[1].strip().split("-")[:2] → "-"-joined`), and asserts
  every row normalizes to the `XX-YY` / `RETRO-XX` pattern — proving the
  normalization is sufficient for the real data (e.g. `12-01-qa-config-contract`
  → `12-01`).