# Story 25-03 — History Dialog: Preserve, Baseline, or Ignore Project History

Status: Planned
Feature: Project Profile & QA Configuration (F-025)

## Context / Purpose

When an existing project is onboarded via `/migrate`, it arrives with a development history. That history lives in git commits, a CHANGELOG.md, a TODO.md, old README sections, or simply in the developer's head. The pipeline currently offers a Phase 5 "retro stories" step, but it never asks the user what they actually want to do with this history — it just runs `create_retro_stories.py` from git-log data if the user says yes.

Three legitimate strategies exist:

1. **Granular retro stories** — analyze git history and existing docs (CHANGELOG, TODO, README) and generate one done story per logical feature/milestone. Gives full traceability. Good for projects with meaningful commit history.
2. **Baseline story** — create a single `00-00-baseline-existing-state.md` story marked done that says "everything that existed before the pipeline was adopted". Good for large legacy codebases where granular reconstruction is impractical.
3. **Clean start** — ignore the history entirely. The git history remains, but the pipeline has no done stories. Good when the existing code is a throwaway or the history is too messy to be meaningful.

Today, `create_retro_stories.py` only reads git-log — it ignores CHANGELOG, TODO, and README history. The migrate skill Phase 5 dialog is a stub. This story implements the full three-option dialog and extends `create_retro_stories.py` to read doc-based history in addition to git.

## Requirements

**`skills/migrate-project.md` Phase 5 dialog:**

The Architect presents a summary of what history was found:
- Git: number of commits, date range, first/last message
- Docs: which of CHANGELOG.md / TODO.md / README.md exist and have history-like content

Then asks: "How do you want to handle the project's existing history?"

Options:
1. **Granular retro stories** — generate one done story per detected milestone (from git + docs)
2. **Single baseline story** — create one `00-00-baseline` story covering everything before pipeline adoption
3. **Clean start** — no retro stories; note in STORIES.md that pipeline adoption date is the starting point

The Architect confirms the chosen option before executing it.

**`scripts/create_retro_stories.py` extension — doc-based history:**

Add a `scan_history(target: Path) -> dict` function that collects:
- `git_summary`: `{commits: int, date_range: [first, last], messages: [last 10 commit subjects]}`
- `changelog_entries`: list of heading strings from `CHANGELOG.md` if it exists (e.g. `["## v1.2.0", "## v1.1.0"]`)
- `todo_items`: list of non-empty lines from `TODO.md` if it exists
- `readme_history_section`: content of a `## History` or `## Changelog` section in `README.md` if present

This scan output is passed to the Architect for the Phase 5 dialog summary. It is also used when building granular retro stories — changelog headings become story titles if no git-derived titles are better.

**Baseline story generation:**

Add `create_baseline_story(target: Path, summary: str) -> dict` to `create_retro_stories.py`. It writes:
```
docs/features/F-RETRO-retro/stories/00-00-baseline-existing-state.md
```
with Status: Done, a summary section from the `summary` argument, and a note that this covers all development before pipeline adoption. Returns `{"created": ["00-00-baseline-existing-state.md"]}` or `{"skipped": [...]}` if already exists.

**Clean start:**

No story files are created. `create_retro_stories.py` is not called. The Architect adds a comment line to `STORIES.md`:
```
<!-- Pipeline adopted: <date>. No retro stories created. Git history preserved. -->
```

**`validate_migration.py` — no new check needed** for this story (history handling is a user choice, not a structural requirement).

## Developer Targets (exactly, no more / no less)

- `scripts/create_retro_stories.py` — add `scan_history(target: Path) -> dict` function (git summary + doc scan); add `create_baseline_story(target: Path, summary: str) -> dict` function; update module docstring to document all three history strategies.
- `skills/migrate-project.md` — replace Phase 5 stub with full three-option dialog: present scan summary, offer granular/baseline/clean-start, confirm before executing; document which script function to call for each option. Update skill header comment.
- `tests/test_create_retro_stories.py` — add tests for `scan_history` (git present, git absent, CHANGELOG present, TODO present, README history section); add tests for `create_baseline_story` (creates file, correct content, no-overwrite).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `scan_history()` returns `git_summary`, `changelog_entries`, `todo_items`, `readme_history_section` keys.
- `scan_history()` works when git is absent (returns empty git_summary).
- `scan_history()` works when CHANGELOG.md / TODO.md / README.md are absent (returns empty lists/strings).
- `create_baseline_story()` creates `00-00-baseline-existing-state.md` with Status: Done.
- `create_baseline_story()` does not overwrite an existing baseline story.
- `skills/migrate-project.md` Phase 5 documents all three options (granular / baseline / clean-start).
- `skills/migrate-project.md` Phase 5 documents calling `scan_history()` before presenting the dialog.
- `skills/migrate-project.md` Phase 5 documents the clean-start STORIES.md comment format.
- All existing tests still pass (no regression).

## Test criteria (must exist BEFORE implementation)

- `tests/test_create_retro_stories.py::test_scan_history_with_git` — project with git repo → `git_summary` has `commits`, `date_range`, `messages`
- `tests/test_create_retro_stories.py::test_scan_history_without_git` — project without `.git` → `git_summary` has zeros/empty values, no error
- `tests/test_create_retro_stories.py::test_scan_history_with_changelog` — project with `CHANGELOG.md` containing headings → `changelog_entries` is non-empty list
- `tests/test_create_retro_stories.py::test_scan_history_without_docs` — project with no CHANGELOG/TODO/README → all doc fields empty, no error
- `tests/test_create_retro_stories.py::test_scan_history_with_todo` — project with `TODO.md` → `todo_items` is non-empty list
- `tests/test_create_retro_stories.py::test_scan_history_readme_history_section` — `README.md` with `## History` section → `readme_history_section` non-empty
- `tests/test_create_retro_stories.py::test_create_baseline_story_creates_file` — creates `00-00-baseline-existing-state.md` with Status: Done and summary content
- `tests/test_create_retro_stories.py::test_create_baseline_story_no_overwrite` — existing baseline → returns skipped, file unchanged
