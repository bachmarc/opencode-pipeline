# Story 37-03 — Plugin Prompt Stories-md Deletion

Status: Done (merged as 54bbddb)
Feature: eliminate-stories-md (F-037)

## Codebase Snapshot

- `plugins/guards/story-status-guard.ts` — 52 lines. Checks if STORIES.md was updated
  after a merge (L7, L31–52). Becomes obsolete: F-033/33-01 writes `Status: Done` to
  story files on every merge — the guard's purpose is superseded.
- `plugins/guards/dev-start-guard.ts` — reads STORIES.md at L73–108 to validate story
  IDs and check story status before dev starts. Must switch to scanning story files.
- `agents/architect.md` — L93 (`STORIES.md` in architect-editable files list), L118
  (conflict candidates → STORIES.md phase block), L147 (reference pattern).
- `templates/AGENTS.md` — references STORIES.md as the story index.
- `AGENTS.md` (root) — references section with `STORIES.md — story index`.
- `APP_VERSION.py` — L3 comment mentions STORIES.md.
- `tests/test_story_status_guard.py` — 1 test checking guard reads STORIES.md (L28–L32).
- `tests/test_dev_start_guard.py` — tests reading STORIES.md for story ID validation
  (L26, L31, L46, L60, L68, L93).
- `tests/test_migration.py` — 2 tests asserting STORIES.md exists and has no REQ-/Design§
  (L181–L229). These should be adapted to FEATURES.md or removed.
- `tests/test_agent_profile_awareness.py` — asserts STORIES.md mentioned in architect.md
  (L116–L120).
- `tests/test_check_scripts.py` — embedded AGENTS.md template text references STORIES.md
  (L118, L155–L156).
- `STORIES.md` — the file itself, to be deleted.

**Prerequisite:** Runs after W1 fully merged (F-034/34-01 touches architect.md).
Runs in parallel with F-033/33-03 and F-033/33-04 (file-disjoint).

## Context / Purpose

After STORIES.md is no longer maintained by scripts (37-02), the remaining references
live in plugins, prompts, tests, and the file itself. This story:
1. Removes `story-status-guard.ts` (obsoleted by F-033/33-01 writing story-file status).
2. Updates `dev-start-guard.ts` to scan story files instead of STORIES.md for story ID
   validation.
3. Updates agent prompts and templates to reference FEATURES.md + story files (no STORIES.md).
4. Updates tests accordingly.
5. Deletes STORIES.md.

## Requirements

1. `plugins/guards/story-status-guard.ts` is deleted. Its test is removed or updated
   to verify the guard no longer exists.
2. `plugins/guards/dev-start-guard.ts` story-ID validation switches from reading STORIES.md
   to scanning `docs/features/*/stories/*.md` filenames for known story IDs.
3. `agents/architect.md`:
   - L93: remove `STORIES.md` from architect-editable files list (story files are edited
     by `merge_if_passed.py`, not the architect directly).
   - L118: replace "STORIES.md phase block" with "feature.md wave declaration".
   - L147: replace `vokabel/STORIES.md` pattern reference with `vokabel/FEATURES.md`.
4. `templates/AGENTS.md`: replace STORIES.md reference with FEATURES.md + story files.
5. `AGENTS.md` (root) References section: replace `STORIES.md — story index` with
   `FEATURES.md — feature index` and add `docs/features/*/stories/*.md — story files`.
6. `APP_VERSION.py` L3: replace STORIES.md with FEATURES.md in comment.
7. `STORIES.md`: deleted.
8. All affected tests updated.

## Developer Targets (exactly, no more / no less)

- `plugins/guards/story-status-guard.ts`: delete file.
- `plugins/guards/dev-start-guard.ts`: replace STORIES.md scan with story-file scan
  (requirement 2); update module comment.
- `agents/architect.md`: requirements 3a/3b/3c.
- `templates/AGENTS.md`: requirement 4.
- `AGENTS.md` (root): requirement 5.
- `APP_VERSION.py`: requirement 6.
- `STORIES.md`: delete.
- `tests/test_story_status_guard.py`: remove test (guard deleted) or replace with
  `test_story_status_guard_file_removed` that asserts the file does not exist.
- `tests/test_dev_start_guard.py`: update STORIES.md-reading tests to reflect story-file
  scanning; remove tests that assert STORIES.md is read.
- `tests/test_migration.py`: remove or adapt STORIES.md-existence tests (L181–L229);
  replace with FEATURES.md-existence check if appropriate.
- `tests/test_agent_profile_awareness.py`: update STORIES.md assertion to FEATURES.md
  or story-files reference.
- `tests/test_check_scripts.py`: update embedded template text to not assert STORIES.md.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `story-status-guard.ts` does not exist.
- `dev-start-guard.ts` validates story IDs by scanning story files, not STORIES.md.
- `agents/architect.md` contains no reference to STORIES.md.
- `templates/AGENTS.md` contains no reference to STORIES.md.
- `STORIES.md` does not exist in the repo root.
- All updated tests pass.

## Test criteria (must exist BEFORE implementation)

QA may augment or correct these criteria during the QA phase.

- `test_story_status_guard_file_removed` — `plugins/guards/story-status-guard.ts`
  does not exist (the file was deleted).
- `test_dev_start_guard_uses_story_files_not_stories_md` — `dev-start-guard.ts`
  source does not contain `STORIES.md` (reads story files instead).
- `test_architect_md_no_stories_md_reference` — `agents/architect.md` does not
  contain the string `STORIES.md`.
- `test_templates_agents_md_no_stories_md_reference` — `templates/AGENTS.md` does not
  contain `STORIES.md`.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (configured checkers in `qa_config.json`)
- [ ] Lint clean (ruff for .py; eslint/tsc for .ts if configured)
- [ ] Typecheck clean (mypy / tsc)
- [ ] Format check clean (black / prettier)
- [ ] Audit clean — n/a
