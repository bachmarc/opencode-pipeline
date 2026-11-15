# Story 33-04 — Plan Check Status Guards

Status: Planned
Feature: driver-trustworthiness (F-033)

## Codebase Snapshot

- `scripts/plan_check.py` — `_parse_story()` L185, `_story_id()` L180, `main()` L247;
  total 379 lines. Current checks: ghost references, same-file conflicts, clarification
  markers, missing required sections. No status-line check, no duplicate-ID check,
  no legacy baseline.
- `tests/test_plan_check.py` — 10 tests; `test_done_stories_skipped` L148,
  `test_clean_story_passes` L77, `test_missing_section_fails` L136.

## Context / Purpose

Three `plan_check.py` gaps from the defect report:
- **D-3 (missing Status line):** a story file with no `Status:` line has `status = ""`
  which `driver.py` treats as "skip" but `plan_check.py` does not flag — silent gap.
- **D-5 (duplicate story IDs):** two story files sharing the same numeric ID prefix
  (e.g., two `48-26-*.md` files) cause duplicate driver actions; `plan_check.py`
  does not detect this.
- **D-9 (legacy noise):** on a mature project, plan_check emits hundreds of
  `missing-section` findings for legacy stories — real new findings drown. A `--since`
  option lets the user scope the check to recent stories only.

## Requirements

1. **D-3:** `plan_check.py` flags any non-Done story file that lacks a `Status:` line
   as a `missing-status-line` problem (blocking, same severity as `missing-section`).
   Done stories (status starts with `done`, case-insensitive) are still skipped entirely.
2. **D-5:** `plan_check.py` detects duplicate story IDs across all scanned story files:
   two files with the same `XX-YY` numeric prefix (e.g., `33-01-foo.md` and
   `33-01-bar.md`) produce a `duplicate-story-id` problem listing both paths.
   STORIES.md row deduplication is out of scope (story files only).
3. **D-9:** new CLI flag `--since <story-id>` (e.g. `--since 30-01`) causes `plan_check.py`
   to skip story files whose numeric ID is less than the given ID. Stories with IDs ≥
   the given ID are checked as normal. The flag applies only to `missing-section` and
   `missing-status-line` findings; ghost-ref and conflict-candidate checks always scan all
   stories regardless of `--since`.
4. All new checks are included in the JSON output `problems` array with a `finding` key
   identifying the check type (`missing-status-line`, `duplicate-story-id`).
5. Module docstring updated to document the new checks and the `--since` flag.

## Developer Targets (exactly, no more / no less)

- `scripts/plan_check.py`:
  - In `_parse_story()` or `main()`: detect missing `Status:` line; add
    `missing-status-line` to problems when absent on non-Done stories.
  - After scanning all stories: build an ID→paths map; emit `duplicate-story-id` problem
    for any ID with more than one path.
  - Add `--since` CLI argument (string, optional); implement skip logic for
    `missing-section` and `missing-status-line` only.
  - Update module docstring.
- `tests/test_plan_check.py`:
  - `test_missing_status_line_flagged` — story file without a `Status:` line produces
    `missing-status-line` problem.
  - `test_done_story_missing_status_not_flagged` — a Done story with no `Status:` line
    is silently skipped (no problem).
  - `test_duplicate_story_id_flagged` — two files `33-01-foo.md` and `33-01-bar.md`
    produce a `duplicate-story-id` problem listing both paths.
  - `test_since_flag_skips_older_stories` — with `--since 33-01`, story `32-05-*.md`
    gets no `missing-section` finding; story `33-01-*.md` still gets checked.
  - `test_since_flag_does_not_skip_ghost_refs` — ghost refs are reported even for
    stories older than the `--since` threshold.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- Missing `Status:` line on a non-Done story → `missing-status-line` finding in JSON output.
- Two files with the same numeric ID prefix → `duplicate-story-id` finding.
- `--since <id>` suppresses `missing-section`/`missing-status-line` for older stories but
  not ghost-ref or conflict-candidate findings.
- All 10 existing `test_plan_check.py` tests still pass.
- `test_f030_self_check_each_story_exit_zero` still passes (no regressions on own stories).

## Test criteria (must exist BEFORE implementation)

- `test_missing_status_line_flagged` — no Status line → `missing-status-line` problem.
- `test_done_story_missing_status_not_flagged` — Done story without Status silently skipped.
- `test_duplicate_story_id_flagged` — two `33-01-*.md` files → `duplicate-story-id` problem.
- `test_since_flag_skips_older_stories` — `--since 33-01` skips `32-05` missing-section.
- `test_since_flag_does_not_skip_ghost_refs` — ghost refs still reported for old stories.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy)
- [ ] Format check clean (black)
- [ ] Audit clean — n/a (no package registry)
