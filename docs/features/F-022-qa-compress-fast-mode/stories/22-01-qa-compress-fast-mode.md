# Story 22-01 — qa_compress.py --fast: changed files → affected test modules

Status: Planned
Feature: qa-compress-fast-mode (F-022)

## Context / Purpose

`qa_compress.py` has no scope filter. Every run executes all 366+ tests (~85s). For a
2-file change, only 2-3 test modules are relevant. A `--fast` flag should detect changed
files via `git diff main..<branch> --name-only`, map them to test modules by name
convention, and pass only those to pytest.

## Requirements

1. `qa_compress.py --fast` detects changed files via `git diff main..<branch> --name-only`
   (falls back to `git diff HEAD~1 --name-only` if not on a feature branch).
2. Mapping convention: `scripts/foo.py` → `tests/test_foo.py`,
   `plugins/guards/foo.ts` → `tests/test_foo.py`, `plugins/foo.ts` → `tests/test_foo.py`.
   Files with no matching test module are ignored (no error).
3. If no test modules are found (e.g., only doc changes), `--fast` falls back to full run
   with a warning.
4. Full run (no flag) is unchanged.
5. `--fast` output clearly labels itself:
   `[fast mode] running: tests/test_foo.py tests/test_bar.py`

## Developer Targets (exactly, no more / no less)

- `scripts/qa_compress.py`: add `--fast` argument to argparse; implement
  `get_changed_test_modules(branch)` function that runs `git diff`, maps filenames to
  test modules, returns list of existing test files; if list non-empty pass to pytest as
  positional args, else fall back to full run with warning. Update module docstring.
- `tests/test_qa_compress.py`: add tests:
  - `test_fast_mode_maps_scripts_to_tests`: mock `git diff` output with
    `scripts/merge_if_passed.py` → assert `tests/test_merge_if_passed.py` in result
  - `test_fast_mode_maps_plugin_guards`: mock `git diff` output with
    `plugins/guards/merge-guard.ts` → assert `tests/test_merge_guard.py` in result
    (if file exists, else skip)
  - `test_fast_mode_fallback_on_no_match`: mock `git diff` output with `README.md` only
    → assert fallback to full run

## Acceptance criteria (checked by qa-manager)

- `qa_compress.py --fast` exists and runs without error.
- `get_changed_test_modules()` function exists in `qa_compress.py`.
- `test_fast_mode_maps_scripts_to_tests` passes.
- `test_fast_mode_fallback_on_no_match` passes.
- Full run (no `--fast`) unchanged — all existing tests still pass.

## Test criteria (must exist BEFORE implementation)

- `tests/test_qa_compress.py::test_fast_mode_maps_scripts_to_tests`: mock subprocess for
  git diff returning `scripts/merge_if_passed.py\n` → `get_changed_test_modules()` returns
  list containing `tests/test_merge_if_passed.py`.
- `tests/test_qa_compress.py::test_fast_mode_fallback_on_no_match`: mock git diff
  returning `README.md\n` → function returns empty list (triggers fallback).
