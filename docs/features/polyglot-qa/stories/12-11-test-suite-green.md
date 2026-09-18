# Story 12-11 — Test-suite green: fix pre-existing failures on main

Status: Planned
Feature: polyglot-qa (F-008)

## Context / Purpose

Three test failures pre-exist on `main` and block every QA gate run (the
qa-manager verifies the full suite deterministically — red suite = FAIL for
any story). Two are code bugs the architect may not touch (architect writes
no code), one docs bug has already been fixed on main by the architect
(missing `req:` frontmatter field — commits e0d7c0d, a8e0848). This story
fixes the two remaining code bugs so the suite is green again and the Phase 12
pipeline (stories 12-01..12-10) can pass QA.

## Requirements

1. `tests/test_feature_hierarchy.py::test_feature_dirs_exist` FAILs:
   the test maps FEATURES.md IDs to directory names via a hardcoded dict
   that lacks the newer features. `F-007` (pipeline-enforcement) and
   `F-008` (polyglot-qa) fall through to the naive fallback
   `feature_id.lower()` (`f-007`/`f-008`), which don't exist.
   Fix: make the ID→directory mapping data-driven — derive the directory
   from the `docs/features/*/feature.md` frontmatter `id:` field instead
   of a hardcoded dict (read each feature.md, build id→dirname map). This
   removes the need to touch the test for every future feature.
2. `tests/test_qa_scripts.py::test_commit_metadata_format` FAILs:
   `scripts/prepare_commit_metadata.py::run_pytest()` invokes
   `["python", "-m", "pytest", ...]`, but this machine has no `python`
   binary (only `python3`); `sys.executable` is the portable choice.
   Fix: replace `"python"` with `sys.executable` in the subprocess call.

## Developer Targets (exactly, no more / no less)

- In `tests/test_feature_hierarchy.py`: replace the hardcoded
  `id_to_dir` dict in `test_feature_dirs_exist` with a frontmatter-driven
  lookup — glob `docs/features/*/feature.md`, parse the `id:` line from
  each frontmatter block, build `{id: dirname}` from the parent dir name.
  Keep the assertion semantics identical (every FEATURES.md row must have
  a matching directory).
- In `scripts/prepare_commit_metadata.py`: `run_pytest()` — change
  `["python", "-m", "pytest", "--tb=no", "-q"]` to
  `[sys.executable, "-m", "pytest", "--tb=no", "-q"]` (`sys` is already
  imported; verify).
- No other changes.

## Acceptance criteria (checked by qa-manager)

- `pytest tests/test_feature_hierarchy.py` fully green (7/7).
- `pytest tests/test_qa_scripts.py` fully green.
- Full suite `pytest tests/` green (no pre-existing failures remaining).
- Changes limited to the two files above; no unrelated refactoring.

## Test criteria (must exist BEFORE implementation)

The failing tests ARE the test criteria (red-first, then green):

- `tests/test_feature_hierarchy.py::test_feature_dirs_exist` — red on
  current main (missing dirs for F-007/F-008 mapping), green after fix.
- `tests/test_qa_scripts.py::test_commit_metadata_format` — red on current
  main (`python` binary not found), green after fix.
- Both tests keep their exact assertion semantics (no weakening of
  assertions — the fix is in the production script, not the test).