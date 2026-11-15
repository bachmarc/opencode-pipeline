# Story 37-02 — Script Stories-md Removal

Status: Done (merged as 7765969)
Feature: eliminate-stories-md (F-037)

## Codebase Snapshot

- `scripts/check_watermark.py` — `get_done_stories(stories_path)` L47 reads STORIES.md
  to extract done story IDs (parses `✅` rows). `check_file()` L114 calls it. Total ~190 lines.
- `scripts/create_retro_stories.py` — `_update_stories_md()` L447, `_create_stories_md()` L483,
  `_create_stories_md_content()` L495 create/update STORIES.md during retroactive migration.
- `scripts/provision_structure.py` — creates `STORIES.md` at L170–176 when provisioning
  a new project.
- `scripts/validate_migration.py` — `check_stories_md()` L306 validates STORIES.md exists.
- `scripts/prepare_agents_md.py` — `references_lines.append("- \`STORIES.md\`")` at L140.
- `scripts/analyze_project.py` — `"STORIES.md"` in existing_pipeline_files list at L249.
- `scripts/driver.py` — comments at L75, L516 mention STORIES.md (no functional use).
- `tests/test_watermark.py` — tests using STORIES.md fixture (L113–L114).
- `tests/test_create_retro_stories.py` — tests checking STORIES.md creation (L107, L151–L186).
- `tests/test_provision_structure.py` — tests checking STORIES.md creation (L192–L452).
- `tests/test_validate_migration.py` — tests checking STORIES.md validation (L63, L217–L218).
- `tests/test_prepare_agents_md.py` — asserts STORIES.md reference in output (L82, L119–L120).
- `tests/test_analyze_project.py` — asserts STORIES.md in pipeline files list (L377–L392).

**Prerequisite:** Runs after F-033/33-03 merges (driver.py conflict) and after
F-033/33-01 merges (check_watermark.py reads Done status from story files, which
33-01 makes reliable).

## Context / Purpose

Seven scripts reference STORIES.md either by reading it or by creating/validating it.
After STORIES.md is deleted (story 37-03), these scripts would break. This story updates
each script to work without STORIES.md:

- `check_watermark.py`: replace STORIES.md-based done-story extraction with story-file
  scanning (same `Status: Done*` lines that driver.py already reads and 33-01 maintains).
- `create_retro_stories.py`: stop creating/updating STORIES.md (retro stories are tracked
  via feature.md + story files, same as all other stories).
- `provision_structure.py`: stop creating STORIES.md for new projects.
- `validate_migration.py`: check for FEATURES.md instead of STORIES.md (FEATURES.md is
  now the top-level index).
- `prepare_agents_md.py`: replace STORIES.md reference with FEATURES.md.
- `analyze_project.py`: remove STORIES.md from the pipeline-files detection list.
- `driver.py`: remove STORIES.md mention from comments (no functional change).

## Requirements

1. `check_watermark.py` `get_done_stories()` is rewritten: scans
   `docs/features/*/stories/*.md` for `Status: Done*` lines (case-insensitive prefix),
   returns story IDs. No longer reads STORIES.md. Module docstring updated.
2. `create_retro_stories.py`: remove `_update_stories_md()`, `_create_stories_md()`,
   and `_create_stories_md_content()` functions and all call sites. Retro stories are
   self-contained in feature.md + story files only. Module docstring updated.
3. `provision_structure.py`: remove the `STORIES.md` creation block. New projects no
   longer get a STORIES.md. Module docstring updated.
4. `validate_migration.py`: `check_stories_md()` replaced by `check_features_md()` —
   validates that FEATURES.md exists (not STORIES.md). Module docstring updated.
5. `prepare_agents_md.py`: replace `"- \`STORIES.md\` — story index (status per story)"`
   with `"- \`FEATURES.md\` — feature index (feature status and story list)"`.
6. `analyze_project.py`: remove `"STORIES.md"` from the pipeline-files list.
7. `scripts/driver.py`: update comments at L75 and L516 to remove STORIES.md mention
   (replace with "story files" or simply remove the parenthetical).
8. All affected tests updated to match the new behaviour.

## Developer Targets (exactly, no more / no less)

- `scripts/check_watermark.py`: rewrite `get_done_stories()` (requirement 1).
- `scripts/create_retro_stories.py`: remove STORIES.md functions (requirement 2).
- `scripts/provision_structure.py`: remove STORIES.md creation (requirement 3).
- `scripts/validate_migration.py`: replace `check_stories_md` → `check_features_md` (req 4).
- `scripts/prepare_agents_md.py`: update reference line (requirement 5).
- `scripts/analyze_project.py`: remove `"STORIES.md"` from list (requirement 6).
- `scripts/driver.py`: comment-only update (requirement 7).
- `tests/test_watermark.py`: update to reflect story-file-based done detection.
- `tests/test_create_retro_stories.py`: remove STORIES.md assertions; verify feature.md
  and story files are created instead.
- `tests/test_provision_structure.py`: remove STORIES.md creation assertions.
- `tests/test_validate_migration.py`: replace STORIES.md fixture/assertion with FEATURES.md.
- `tests/test_prepare_agents_md.py`: update reference assertion.
- `tests/test_analyze_project.py`: update pipeline-files assertion.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `check_watermark.py` scans story files for `Status: Done*` (no STORIES.md read).
- `provision_structure.py` no longer creates STORIES.md.
- `validate_migration.py` checks for FEATURES.md, not STORIES.md.
- All updated tests pass.
- STORIES.md is NOT deleted by this story (that is 37-03's job).

## Test criteria (must exist BEFORE implementation)

QA may augment or correct these criteria during the QA phase.

- `test_watermark_reads_story_files_not_stories_md` — `get_done_stories()` returns
  correct IDs from story files; does not open STORIES.md.
- `test_provision_does_not_create_stories_md` — provisioned project has no STORIES.md.
- `test_validate_migration_checks_features_md` — validate_migration passes when
  FEATURES.md exists; fails when FEATURES.md absent (regardless of STORIES.md).
- `test_retro_stories_no_stories_md_update` — create_retro_stories run produces no
  STORIES.md; feature.md + story files are created.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy)
- [ ] Format check clean (black)
- [ ] Audit clean — n/a
