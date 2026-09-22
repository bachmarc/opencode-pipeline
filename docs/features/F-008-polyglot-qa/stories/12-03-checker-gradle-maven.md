# Story 12-03 — Checker plugins: gradle + maven (Java)

Status: Done (QA PASS, 9a08022)
Feature: polyglot-qa (F-008)

## Context / Purpose

Java is daily business for the user; some Java projects use Gradle, others
(especially legacy) use Maven — both must be gateable. Mixed repos may list both.
Same plugin contract as 12-02: one self-registering file per runner in
`scripts/qa_checkers/`, no shared-file edits.

## Requirements

- Checker `gradle`: runs `gradle test` in the project cwd.
  - Summary: line matching `N tests completed, M failed` (if present) or the
    `BUILD SUCCESSFUL` / `BUILD FAILED` line.
  - FAIL detail: lines matching `FAILED` test identifiers (e.g.
    `com.example.BoardTest > rendersBoard() FAILED`), ≤20.
- Checker `maven`: runs `mvn test` in the project cwd.
  - Summary: line matching `Tests run: N, Failures: M, Errors: K, Skipped: S`.
  - FAIL detail: lines matching `<<< FAILURE!` (test identifier before the
    marker, e.g. `Tests run: ... BoardTest.rendersBoard <<< FAILURE!`), ≤20.
- Both follow the 12-01 plugin contract (`register_check` at file end).
- No changes to `qa_compress.sh` or existing plugin files.

## Developer Targets (exactly, no more / no less)

- `scripts/qa_checkers/gradle.sh`: `gradle_check()` — runs `gradle test`;
  summary grep for `tests completed` or `BUILD (SUCCESSFUL|FAILED)`; on
  non-zero exit print `## failed_tests` + lines matching `FAILED$| FAILED`
  excluding the BUILD line (tail -n 20) + `## short_test_summary`; then
  `register_check gradle gradle_check`.
- `scripts/qa_checkers/maven.sh`: `maven_check()` — runs `mvn test`; summary
  grep `^Tests run: `; on failure `## failed_tests` + lines matching
  `<<< FAILURE!` (tail -n 20); then `register_check maven maven_check`.
- `tests/test_qa_checkers_java.py` (see test criteria) — fake `gradle` / `mvn`
  binaries replaying preserved output.

## Acceptance criteria (checked by qa-manager)

- `{"checkers": ["gradle"]}` green → `BUILD SUCCESSFUL` summary, PASS.
- `{"checkers": ["maven"]}` failing → overall FAIL, failing test identifier
  listed.
- Existing checkers (pytest) unchanged; 12-01/12-02 tests green.
- `bash -n` passes for both files; no model/provider names.

## Test criteria (must exist BEFORE implementation)

`tests/test_qa_checkers_java.py` — tmp_path project roots, stub binaries:

- `test_gradle_pass` — fake `gradle` prints
  `> Task :test`, blank, `12 tests completed, 0 failed`, `BUILD SUCCESSFUL`,
  exit 0 → overall PASS, output contains `BUILD SUCCESSFUL`.
- `test_gradle_fail` — fake prints `3 tests completed, 1 failed`,
  `com.example.BoardTest > rendersBoard() FAILED`, `BUILD FAILED`, exit 1 →
  overall FAIL, output contains `BoardTest > rendersBoard() FAILED`.
- `test_maven_pass` — fake `mvn` prints
  `Tests run: 8, Failures: 0, Errors: 0, Skipped: 0`, `BUILD SUCCESS`,
  exit 0 → overall PASS.
- `test_maven_fail` — fake prints
  `Tests run: 3, Failures: 1, Errors: 0, Skipped: 0`,
  `[ERROR] Tests run: 3, Failures: 1 ... in BoardTest`,
  `BoardTest.rendersBoard:15 <<< FAILURE!`, `BUILD FAILURE`, exit 1 →
  overall FAIL, output contains `BoardTest.rendersBoard` under failed_tests.