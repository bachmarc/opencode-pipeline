# Story 19-01 — qa_compress.py: Python QA Entry Point (replaces bash)

Status: Planned
Feature: F-019-python-qa-toolchain (F-019)

## Context / Purpose

`qa_compress.sh` is the only bash file in an otherwise all-Python framework. On Windows,
`bash` is not in PATH → 26 of 354 tests fail with `/bin/bash: … No such file or directory`.
The fix is a Python reimplementation with identical output contract and the same
registry/plugin architecture — so the QA agent sees no difference in output, and new
checkers are still one file each.

The bash files (`qa_compress.sh` and all `qa_checkers/*.sh`) are deleted once the Python
equivalents are in place and all tests pass.

## Requirements

- `scripts/qa_compress.py` exists and is the sole QA entry point (replaces `qa_compress.sh`).
- Output format is identical to the current bash version:
  - Header: `# QA-Testsummary (HH:MM:SS)`
  - Per checker: `## <name> (exit: <N>)` followed by compressed output
  - Footer: `---\noverall: PASS` or `overall: FAIL`
  - Exit code: 0 = PASS, 1 = FAIL
- Registry pattern: `register_check(name: str, fn: Callable) -> None` function in
  `qa_compress.py`; checker modules call it at import time (self-registering).
- Checker discovery: `qa_compress.py` imports all `scripts/qa_checkers/*.py` modules at
  startup (glob + importlib), same as the bash `source` loop.
- `qa_config.json` contract identical: no file → default `["pytest"]`; empty list → opt-out
  PASS; unknown checker → loud FAIL exit 1; invalid JSON → FAIL exit 1.
- 8 checker modules in `scripts/qa_checkers/`: `pytest.py`, `rspec.py`, `jest.py`,
  `gradle.py`, `maven.py`, `json.py`, `yaml.py`, `html.py`.
- Each checker function runs the external tool via `subprocess.run()`, parses output with
  `re`, returns `(compressed_output: str, exit_code: int)`.
- Fake runners in tests are Python scripts (`sys.stdout.write(output); sys.exit(code)`)
  — no bash heredocs, platform-independent.
- `scripts/qa_compress.sh` and all `scripts/qa_checkers/*.sh` are deleted.
- All 26 previously failing tests pass. All previously passing tests remain green.
- `test_qa_checkers_json_yaml.py::test_yaml_missing_pyyaml` is adapted: the stub that
  intercepts `import yaml` becomes a Python wrapper script instead of a bash script.
- `prepare_commit_metadata.py` is NOT changed (it reads `qa_config.json` independently and
  calls runners directly — no dependency on `qa_compress.py`).

## Developer Targets (exactly, no more / no less)

- `scripts/qa_compress.py` — new file. Registry (`CHECKERS` dict), `register_check()`,
  plugin discovery via `importlib` + glob of `qa_checkers/*.py`, `qa_config.json` parsing
  (identical logic to current bash inline Python), checker dispatch loop, output formatting.
  Module header documents the contract (replaces `qa_compress.sh` header comment).
- `scripts/qa_checkers/pytest.py` — new file. `pytest_check()`: runs `pytest --tb=short`,
  extracts summary line (regex `passed|failed|error|no tests`), on failure extracts
  `FAILED`/`ERROR` lines. Calls `register_check("pytest", pytest_check)`.
- `scripts/qa_checkers/rspec.py` — new file. `rspec_check()`: runs `rspec --format
  progress`, extracts `N examples` summary, on failure extracts `rspec ./spec/…` lines.
  Calls `register_check("rspec", rspec_check)`.
- `scripts/qa_checkers/jest.py` — new file. `jest_check()`: runs `jest`, extracts `Tests:`
  summary line, on failure extracts `✕` lines. Calls `register_check("jest", jest_check)`.
- `scripts/qa_checkers/gradle.py` — new file. `gradle_check()`: runs `gradle test`, extracts
  `BUILD SUCCESSFUL/FAILED` + `N tests completed` summary, on failure extracts
  `FAILED` test identifiers (not the BUILD line). Calls `register_check("gradle",
  gradle_check)`.
- `scripts/qa_checkers/maven.py` — new file. `maven_check()`: runs `mvn test`, extracts
  `Tests run:` summary, on failure extracts `[ERROR]` + `FAILURE!` lines. Calls
  `register_check("maven", maven_check)`.
- `scripts/qa_checkers/json.py` — new file. `json_check()`: walks cwd for `*.json`
  (excluding `.git`, `.pipeline`, `.worktrees`, `node_modules`, `__pycache__`,
  `.pytest_cache`, `dist`, `build`, and `qa_config.json` itself), validates each with
  `json.loads()`, reports `N files checked, M invalid`. Calls `register_check("json",
  json_check)`.
- `scripts/qa_checkers/yaml.py` — new file. `yaml_check()`: walks cwd for `*.yaml`/`*.yml`
  (same exclusions), validates each with `yaml.safe_load()`, reports `N files checked, M
  invalid`. If `import yaml` fails → loud FAIL `"yaml checker: PyYAML not installed"`, exit
  1. Calls `register_check("yaml", yaml_check)`.
- `scripts/qa_checkers/html.py` — new file. `html_check()`: walks cwd for `*.html` (same
  exclusions), validates each with `html.parser.HTMLParser` stack discipline (void tags,
  `p` excluded), reports `N files checked, M invalid`. Calls `register_check("html",
  html_check)`.
- `tests/test_qa_config.py` — update: replace `["bash", str(QA_SCRIPT)]` with
  `[sys.executable, str(QA_SCRIPT)]`; update `QA_SCRIPT` to point to `qa_compress.py`;
  replace bash fake-runner scripts with Python fake-runner scripts
  (`#!/usr/bin/env python3\nimport sys\nsys.stdout.write(output)\nsys.exit(code)`).
- `tests/test_qa_checkers_rspec_jest.py` — same updates as above.
- `tests/test_qa_checkers_java.py` — same updates as above.
- `tests/test_qa_checker_html.py` — update `QA_SCRIPT` to `qa_compress.py`; replace
  `["bash", str(QA_SCRIPT)]` with `[sys.executable, str(QA_SCRIPT)]`.
- `tests/test_qa_checkers_json_yaml.py` — update `QA_SCRIPT` and `YAML_PLUGIN` references;
  replace bash invocations with Python; adapt `test_yaml_missing_pyyaml` to use a Python
  wrapper that intercepts `import yaml` (e.g. a `yaml.py` shim on `sys.path`) instead of
  a bash stub.
- `tests/test_commit_metadata_polyglot.py` — update fake runner scripts from bash to Python.
- `scripts/qa_compress.sh` — deleted.
- `scripts/qa_checkers/pytest.sh`, `rspec.sh`, `jest.sh`, `gradle.sh`, `maven.sh`,
  `json.sh`, `yaml.sh`, `html.sh` — all deleted.
- Update docstrings and module headers in every file you change — code documentation is the
  source of truth.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `scripts/qa_compress.sh` does not exist.
- `scripts/qa_checkers/*.sh` do not exist.
- `scripts/qa_compress.py` exists and is executable (`python scripts/qa_compress.py`).
- `scripts/qa_checkers/*.py` — exactly 8 files (pytest, rspec, jest, gradle, maven, json,
  yaml, html).
- All 354 tests pass (0 failures, 0 errors). Previously 26 failed due to `/bin/bash`.
- `test_qa_config.py`, `test_qa_checkers_rspec_jest.py`, `test_qa_checkers_java.py`,
  `test_qa_checker_html.py`, `test_qa_checkers_json_yaml.py` all pass.
- No `bash` invocation remains in any test file for `qa_compress`.

## Test criteria (must exist BEFORE implementation)

All existing tests in the 5 affected test files are the test criteria — they define the
contract. The developer must make them pass by replacing bash with Python, not by changing
the assertions.

Specific contracts verified by tests:
- `test_qa_config.py`: default checker, explicit config, unknown checker, opt-out, invalid
  JSON, fake pytest failure — all 6 scenarios pass with Python runner.
- `test_qa_checkers_rspec_jest.py`: rspec pass/fail, jest pass/fail — 4 tests pass with
  Python fake runners.
- `test_qa_checkers_java.py`: gradle pass/fail, maven pass/fail — 4 tests pass with Python
  fake runners.
- `test_qa_checker_html.py`: html pass, unclosed, mismatch, void tags, excludes dirs — 5
  tests pass.
- `test_qa_checkers_json_yaml.py`: json pass/fail/excludes, yaml pass/fail, yaml missing
  pyyaml — 6 tests pass with Python-based yaml-missing stub.
- `test_commit_metadata_polyglot.py::test_rspec_symbols_and_tests` — passes with Python
  fake rspec runner.
