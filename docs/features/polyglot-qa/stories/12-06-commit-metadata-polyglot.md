# Story 12-06 — Polyglot commit metadata

Status: Planned
Feature: polyglot-qa (F-008)

## Context / Purpose

`scripts/prepare_commit_metadata.py` runs a hard-coded `python -m pytest
--tb=no -q` for the `tests:` field and extracts symbols/dependents
Python-only (AST + `import` grep). In a Ruby/JS/Java project both the test
result and the symbol analysis are wrong. The script must follow the same
runner abstraction as the QA gate: the project's declared checkers decide
what runs — not a hard-wired pytest.

## Requirements

- `tests:` field: runs the project's configured test command instead of
  hard-coded pytest. Source of truth: `qa_config.json` in the project root.
  - No `qa_config.json` → `python -m pytest --tb=no -q` (unchanged default).
  - Configured checkers: the FIRST test-runner checker in the list wins
    (precedence order: `rspec`, `jest`, `gradle`, `maven`, `pytest` — the
    first entry from this order that appears in `checkers`). Syntax checkers
    (`json`, `yaml`, `html`) never provide `tests:` — if only they are
    configured, `tests: n/a (syntax checkers only)` or the actual syntax
    result.
  - The runner is invoked with its standard quiet invocation from the
    checker plugins (rspec: `rspec`, jest: `jest`, gradle: `gradle test`,
    maven: `mvn test`); last non-empty output line as summary (current
    pytest behavior).
- `symbols:` field: language-appropriate extraction instead of Python-only:
  - `.py` → AST top-level functions/classes (unchanged).
  - `.rb` → `def <name>` / `class <Name>` / `module <Name>` (regex).
  - `.js`/`.ts`/`.jsx`/`.tsx` → `function <name>`, `class <Name>`,
    `const <name> =` (regex).
  - `.java` → `class <Name>`, `interface <Name>` (regex).
  - Other → file stem (unchanged fallback).
- `affects:` field: import/require grep generalized: search for the module
  name (Python import / Ruby require / JS import-require / Java import)
  via one grep pattern per language family.
- Output format unchanged: `symbols: ... | breaks: ... | affects: ... |
  tests: ...`.

## Developer Targets (exactly, no more / no less)

- Rework `scripts/prepare_commit_metadata.py`:
  - `get_test_command(config_checkers: list[str]) -> tuple[str, list[str]]`
    — maps first matching runner checker to its invocation
    (`rspec` → `["rspec"]`, `jest` → `["jest"]`, `gradle` →
    `["gradle", "test"]`, `maven` → `["mvn", "test"]`, `pytest` →
    `["python", "-m", "pytest", "--tb=no", "-q"]`); syntax-only
    configuration → `None`.
  - `run_test(command)` — replaces `run_pytest()`; same summary extraction
    (last non-empty line); command `None` → `tests: n/a (syntax checkers
    only)`.
  - `extract_ruby_symbols`, `extract_js_symbols`, `extract_java_symbols`
    — regex-based, next to existing `extract_python_symbols`.
  - `extract_symbols` dispatches on suffix (`.py` unchanged, new `.rb`,
    `.js`/`.ts`/`.jsx`/`.tsx`, `.java`).
  - `find_dependents` — per-language patterns: Python
    `(from|import)\s+<m>`, Ruby `require.*<m>`, JS
    `(import|require).*<m>`, Java `import.*<m>`.
  - Read `qa_config.json` from repo root (same default logic as 12-01).
- `tests/test_commit_metadata_polyglot.py` (see test criteria).

## Acceptance criteria (checked by qa-manager)

- No `qa_config.json` in a repo with staged `.py` file → output identical to
  current behavior (`tests:` contains pytest summary, `symbols:` contains
  top-level def/class).
- Config `["rspec"]` + staged `.rb` file defining `class Board` + `def move` →
  `symbols:` contains `Board`, `move`; `tests:` from fake rspec binary.
- Config `["jest"]` + staged `.js` file with `function render()` → `symbols:`
  contains `render`.
- Staged `.java` file with `class Board` → `symbols:` contains `Board`.
- Config `["json", "yaml"]` only → `tests: n/a (syntax checkers only)`.
- Format still exactly `symbols: ... | breaks: ... | affects: ... | tests: ...`
  (4 pipe-separated parts — existing `test_commit_metadata_format` green).
- Existing `tests/test_qa_scripts.py` tests for this script stay green.

## Test criteria (must exist BEFORE implementation)

`tests/test_commit_metadata_polyglot.py` — git repos in `tmp_path`, fake
runner binaries on PATH:

- `test_default_python_unchanged` — no config, staged `mod.py` with
  `def run()` + fake `python -m pytest`... (use real python interpreter with
  `--co` or a stub `python` on PATH printing `3 passed`) → `symbols: run`,
  `tests:` non-empty.
- `test_rspec_symbols_and_tests` — config `["rspec"]`, staged `board.rb` with
  `class Board` and `def move`, fake `rspec` printing `10 examples, 0
  failures` → output contains `symbols: Board, move` and `10 examples`.
- `test_js_symbols` — config `["jest"]`, staged `render.js` with
  `function render() {}` → `symbols: render`.
- `test_java_symbols` — config `["maven"]`, staged `Board.java` with
  `class Board {` → `symbols: Board`.
- `test_syntax_only_config` — config `["json", "yaml"]`, staged valid
  `cfg.json` → `tests: n/a (syntax checkers only)`.
- `test_format_unchanged` — any config: output splits into exactly 4
  pipe-separated sections with the known field names.