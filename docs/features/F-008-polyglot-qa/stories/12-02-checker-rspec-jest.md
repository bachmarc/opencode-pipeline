# Story 12-02 — Checker plugins: rspec (Ruby) + jest (JavaScript)

Status: Done
Feature: polyglot-qa (F-008)

## Context / Purpose

Ruby and JavaScript projects cannot be QA-gated: the checker dispatch (12-01)
knows only pytest. This story adds runner checker plugins for the user's two
most common dynamic languages. Each plugin is a self-registering file in
`scripts/qa_checkers/` — no edits to shared files, merge-conflict-free with
parallel checker stories (12-03, 12-04, 12-05).

## Requirements

- Checker `rspec`: runs `rspec --format progress` in the project cwd.
  - PASS summary: last line matching `N examples, M failures` (e.g.
    `47 examples, 0 failures`).
  - FAIL detail: lines matching `rspec ./spec/...rb:LINE # description` from
    the failure list (≤20, like pytest checker).
- Checker `jest`: runs `jest` in the project cwd.
  - Summary: the line matching `Tests: <N passed, M failed, ...>`.
  - FAIL detail: lines starting with `✕ ` (failed test names, ≤20).
- Both plugins follow the 12-01 plugin contract: one file per runner in
  `scripts/qa_checkers/`, registering itself via `register_check <name> <fn>`.
- Exit code of the checker = exit code of the runner subprocess; script
  aggregation (12-01) handles overall FAIL.
- No changes to `qa_compress.sh` itself or any existing plugin file.

## Developer Targets (exactly, no more / no less)

- `scripts/qa_checkers/rspec.sh`: `rspec_check()` — capture output to temp file;
  grep summary line (`[0-9]+ examples`); on non-zero exit print `## failed_tests`
  + lines matching `^rspec \./.*#` (tail -n 20) + `## short_test_summary`
  (same lines, ` - ` suffix stripped); then `register_check rspec rspec_check`.
- `scripts/qa_checkers/jest.sh`: `jest_check()` — analogous; summary line via
  grep `^Tests: `; on failure list lines matching `^✕ ` (tail -n 20) under
  `## failed_tests`; then `register_check jest jest_check`.
- `tests/test_qa_checkers_rspec_jest.py` (see test criteria) — fake `rspec` /
  `jest` binaries on PATH replaying preserved output, `qa_config.json` selects
  the checker.

## Acceptance criteria (checked by qa-manager)

- `{"checkers": ["rspec"]}` with green rspec run → `## rspec (exit: 0)`,
  summary line present, overall PASS.
- rspec failing run → overall FAIL, failed spec file:line listed.
- `{"checkers": ["jest"]}` green → `Tests:` summary, PASS; failing → FAIL with
  `✕` test names.
- Existing pytest behavior unchanged; 12-01 tests still green.
- `bash -n` passes for both new plugin files; no model/provider names in the
  new files.

## Test criteria (must exist BEFORE implementation)

`tests/test_qa_checkers_rspec_jest.py` — fake project roots via `tmp_path`,
stub binaries written to a `bin/` dir prepended to PATH:

- `test_rspec_pass` — config `["rspec"]`; fake `rspec` prints
  `..........`, blank line, `47 examples, 0 failures`, exit 0 → output
  contains `47 examples, 0 failures`, `## rspec (exit: 0)`, overall PASS.
- `test_rspec_fail` — fake prints `F` progress + summary
  `2 examples, 1 failure` + `rspec ./spec/board_spec.rb:12 # does a thing`,
  exit 1 → overall FAIL, output contains `./spec/board_spec.rb:12`.
- `test_jest_pass` — fake `jest` prints `Tests:       4 passed, 4 total`,
  exit 0 → overall PASS, summary line present.
- `test_jest_fail` — fake prints `Tests:       1 failed, 3 passed, 4 total`
  and `✕ renders the board (3 ms)`, exit 1 → overall FAIL, output contains
  `✕ renders the board`.