# Story 12-01 — QA config contract + config-driven checker dispatch

Status: Planned
Feature: polyglot-qa (F-008)

## Context / Purpose

`scripts/qa_compress.sh` hard-registers exactly one checker (`pytest_check`) with
pytest-9-specific output parsing. A project in any other language (Ruby, JavaScript,
Java, mixed) cannot pass the QA gate at all — the gate is effectively Python-only
by accident of wiring. The pipeline needs a deterministic, machine-readable way for
each project to declare which checkers the QA gate must run. Story test criteria
remain the human source for WHAT to test; the config only tells the script WHICH
tools to invoke.

## Requirements

- A committed `qa_config.json` in the project root declares the checkers:
  `{"checkers": ["<name>", ...]}`.
- `qa_compress.sh` reads `qa_config.json` from the current working directory:
  - No `qa_config.json` → default `["pytest"]` (backward compatible, existing
    projects unchanged).
  - Unknown checker name (not registered by any plugin) → loud FAIL with
    `unknown checker: <name>`, exit code 1.
  - Empty list `"checkers": []` → explicit opt-out: output
    `no checkers configured (explicit opt-out)`, overall PASS, exit 0.
  - Invalid JSON in `qa_config.json` → FAIL with error message, exit 1.
- Each checker lives in its own plugin file in `scripts/qa_checkers/` and registers
  itself. `qa_compress.sh` sources all `scripts/qa_checkers/*.sh` after defining the
  registry, then runs exactly the configured checkers serially. Overall semantics
  stay AND: any non-zero checker → overall FAIL.
- The existing `pytest_check` moves unchanged (same parsing) into
  `scripts/qa_checkers/pytest.sh`.
- `python3` may be used inside `qa_compress.sh` for JSON parsing (python3 is a
  framework prerequisite, not a project prerequisite).

## Developer Targets (exactly, no more / no less)

- Create `scripts/qa_checkers/pytest.sh`: contains the existing `pytest_check()`
  function (moved verbatim from `qa_compress.sh`) plus its
  `register_check pytest pytest_check` line.
- Rework `scripts/qa_compress.sh`:
  - Keep `CHECKERS` array + `register_check()` as before.
  - After function/registry definitions: `source` every `scripts/qa_checkers/*.sh`
    (sorted, glob-failure-safe).
  - Read checker list from `qa_config.json` in cwd via `python3 -c` one-liner:
    missing file → `pytest`; invalid JSON → print error, exit 1; valid → print
    space-separated checker names.
  - Validate configured names against the registered registry: unknown name →
    print `unknown checker: <name>`, exit 1.
  - Empty configured list → print `no checkers configured (explicit opt-out)`,
    `overall: PASS`, exit 0.
  - Run only the configured checkers serially with the existing aggregation
    (any non-zero → overall FAIL).
  - Update the script header comment to document the `qa_config.json` contract
    and the plugin mechanism.
- Add `tests/test_qa_config.py` (see test criteria).

## Acceptance criteria (checked by qa-manager)

- No `qa_config.json` + `pytest` runnable → script behaves exactly like before
  (pytest summary in output, exit code of pytest).
- `{"checkers": ["pytest"]}` behaves identically to the default.
- `{"checkers": ["rspec"]}` (rspec plugin not merged yet) → exit 1, output
  contains `unknown checker: rspec`.
- `{"checkers": []}` → exit 0, output contains `no checkers configured`.
- Broken `qa_config.json` → exit 1, output contains an error message (no traceback).
- `bash -n scripts/qa_compress.sh` passes; existing
  `tests/test_framework.py::test_qa_compress_script` passes unchanged.
- Portable files contain no concrete model/provider names (existing check).

## Test criteria (must exist BEFORE implementation)

`tests/test_qa_config.py` — all use `tmp_path` as fake project root, fake binaries
on PATH (stub scripts with preserved output), no real pytest/runner required:

- `test_default_pytest_without_config` — no config file; fake `pytest` binary
  (prints `78 passed`, exit 0) → script output contains `## pytest` and
  `overall: PASS`, exit 0.
- `test_explicit_pytest_config` — config `{"checkers": ["pytest"]}`, same fake →
  identical PASS behavior.
- `test_unknown_checker_fails` — config `{"checkers": ["rspec"]}` → exit 1,
  output contains `unknown checker: rspec`.
- `test_empty_config_optout` — config `{"checkers": []}` → exit 0, output
  contains `no checkers configured (explicit opt-out)` and `overall: PASS`.
- `test_invalid_config_fails` — config file with invalid JSON → exit 1, output
  contains an error message.
- `test_fake_pytest_failure` — config `["pytest"]`, fake binary replays failing
  output (`1 failed`, `FAILED tests/x.py::test_a - assert ...`) → overall FAIL,
  output contains `failed_tests` and the test name.