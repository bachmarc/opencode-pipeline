# Story 27-04 — Ruby/Java Lint Checkers: rubocop, checkstyle

Status: Planned
Feature: Tooling-Gate Bootstrap (F-027)

## Codebase Snapshot

- `scripts/qa_compress.py` — `rspec_check()` at line 124 is the reference for Ruby tool
  invocation (uses `bundle exec rspec`). `gradle_check()` at line 217 is reference for Java.
  CHECKERS dict at lines ~563–578.
- `scripts/qa_checkers/rspec.py` — dead code, do not use.
- `tests/` — fake-binary test pattern for reference.

## Context / Purpose

Ruby projects use RuboCop for both linting and formatting (one tool, both concerns).
A project declaring `{"checkers": ["rspec", "rubocop"]}` would crash on "unknown checker".

Java projects use Checkstyle for static analysis. A project declaring
`{"checkers": ["gradle", "checkstyle"]}` should work.

Both follow the same inline pattern as all other checkers.

## Requirements

1. `rubocop_check()` — runs `bundle exec rubocop` (preferred, uses Gemfile-locked version)
   falling back to `rubocop` on PATH. Not found: `"rubocop not found\n"`, exit 1.
   Compressed output: offense count + first 20 offense lines on failure.
   On success: `"rubocop: 0 offenses\n"`.

2. `checkstyle_check()` — runs Checkstyle via `./gradlew checkstyleMain checkstyleTest`
   if `gradlew` present, otherwise `mvn checkstyle:check`, otherwise `checkstyle` on PATH.
   Not found/not applicable: `"checkstyle not found (no gradlew, mvn, or checkstyle binary)\n"`, exit 1.
   Compressed output: violation count + first 20 violations on failure.
   On success: `"checkstyle: 0 violations\n"`.

3. Both registered in `CHECKERS` dict as `"rubocop"`, `"checkstyle"`.

## Developer Targets (exactly, no more / no less)

- `scripts/qa_compress.py`: Add two inline checker functions after `black_check()`:
  - `rubocop_check() -> tuple[str, int]`
  - `checkstyle_check() -> tuple[str, int]`
  Add to CHECKERS dict: `"rubocop": rubocop_check`, `"checkstyle": checkstyle_check`.
  Update module docstring.

- `tests/test_qa_checkers_ruby_java_lint.py` (new file): 6 tests minimum (3 per checker).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `qa_compress.py` CHECKERS dict contains `"rubocop"`, `"checkstyle"`.
- `rubocop_check()` tries `bundle exec rubocop` first, then `rubocop`.
- `checkstyle_check()` tries gradlew, then mvn, then binary.
- Each checker: clear "not found" exit 1. Compressed output, not raw log.
- All 6+ tests pass. No existing tests broken.

## Tooling Gates (mandatory — QA checks ALL of these)

- [ ] Tests green (`pytest`)
- [ ] Lint clean — N/A
- [ ] Typecheck clean — N/A
- [ ] Format check clean — N/A
- [ ] Audit clean — N/A

## Test criteria (must exist BEFORE implementation)

- `test_rubocop_check_success` — fake `rubocop` exits 0 → exit 0, "0 offenses".
- `test_rubocop_check_failure` — fake `rubocop` exits 1 with offenses → exit 1, offense lines.
- `test_rubocop_check_not_found` — no rubocop/bundle → exit 1, "not found".
- `test_checkstyle_check_success` — fake `gradlew checkstyleMain checkstyleTest` exits 0 → exit 0, "0 violations".
- `test_checkstyle_check_failure` — fake `gradlew` exits 1 with violations → exit 1, violation lines.
- `test_checkstyle_check_not_found` — no gradlew/mvn/checkstyle → exit 1, "not found".
