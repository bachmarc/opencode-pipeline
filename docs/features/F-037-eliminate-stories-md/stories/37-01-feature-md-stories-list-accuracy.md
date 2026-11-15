# Story 37-01 — Feature-md Stories List Accuracy

Status: Planned
Feature: eliminate-stories-md (F-037)

## Codebase Snapshot

- `docs/features/F-*/feature.md` — each has a `## Stories` section listing story IDs.
  These are hand-maintained and may be stale. 36 feature files exist.
- `tests/test_framework.py` — framework invariant tests. Add new test here.

## Context / Purpose

STORIES.md is being eliminated (F-037). Before deletion, every feature.md must be
self-sufficient: its `## Stories` section must accurately list the stories that actually
exist in its `stories/` directory. Today, some feature.md files have wrong or missing
story IDs (leftover from create_story.py generating `01-xx` IDs that were manually
corrected in story files but not in feature.md, or stories added without updating
feature.md). This story is a prerequisite for F-037/37-02 and 37-03: ensures that
after STORIES.md is deleted, feature files are a reliable navigation index.

## Requirements

1. Every `docs/features/F-*/feature.md` `## Stories` section lists exactly the story IDs
   that exist as `.md` files in its `stories/` subdirectory — no extras, no missing.
2. Story IDs in the list use the actual filename prefix (e.g. `33-01`, not `01-01`).
3. A new pytest test `test_feature_md_stories_match_files` in `tests/test_framework.py`
   verifies requirement 1 for ALL feature directories: for each feature, parse the
   `## Stories` section and compare against actual `.md` filenames. Fail with a clear
   message listing mismatches.
4. Feature.md Context sections are reviewed: where a Context section is a single sentence
   or clearly minimal (less than 2 genuine sentences about the problem and solution), it
   is expanded to 2–3 sentences adequately explaining why the feature exists and what
   problem it solved. Developer reads each feature.md Context and expands where clearly
   insufficient; the STORIES.md phase block is the reference for missing narrative.

## Developer Targets (exactly, no more / no less)

- `docs/features/F-*/feature.md` (all 36 files):
  - Fix `## Stories` section to match actual story files (requirement 1 + 2).
  - Expand Context section where clearly insufficient (requirement 4).
- `tests/test_framework.py`:
  - `test_feature_md_stories_match_files` — for each feature dir, parse `## Stories`
    section, compare IDs against filenames in `stories/`, assert no mismatches.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `test_feature_md_stories_match_files` passes for all 36+ feature directories.
- No feature.md has a story listed that doesn't exist as a file, and vice versa.
- All existing `tests/test_framework.py` tests still pass.

## Test criteria (must exist BEFORE implementation)

QA may augment or correct these criteria during the QA phase.

- `tests/test_framework.py::test_feature_md_stories_match_files` — parses each
  feature.md `## Stories` section, compares IDs against `stories/*.md` filenames,
  fails with a clear diff on any mismatch.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean — n/a (mostly docs edits + one test function)
- [ ] Typecheck clean — n/a
- [ ] Format check clean (black — for test_framework.py)
- [ ] Audit clean — n/a
