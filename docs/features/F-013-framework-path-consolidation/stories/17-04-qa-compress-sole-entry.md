# Story 17-04 — qa_compress.sh as Sole Test Entry Point

Status: Planned
Feature: F-013-framework-path-consolidation (F-013)

## Context / Purpose

`developer.md` and `qa-manager.md` currently allow (and in some places instruct) direct
`pytest` calls. `qa_config.json` can configure multiple checkers (e.g. `["pytest", "yaml"]`),
but only `qa_compress.sh` reads this file and runs all configured checkers. Direct `pytest`
silently skips all non-pytest checkers.

The fix: prompts must describe `qa_compress.sh` as the sole test runner. Direct `pytest` is
only mentioned as a checker name in the `qa_config.json` context — never as a command to run.

`qa_compress.sh` already self-localizes via `$(dirname "${BASH_SOURCE[0]}")/qa_checkers` —
this is the correct pattern. Prompts must reference it by name without a hardcoded path
(since the path is framework-installation-dependent and platform-specific).

## Requirements

- `agent/developer.md`: replace all direct `pytest` run instructions with "run the test suite
  via `qa_compress.sh`". No hardcoded path to `qa_compress.sh` — describe it as "the
  framework's test runner script".
- `agent/qa-manager.md`: same — replace direct `pytest` with `qa_compress.sh` description.
- Neither file contains a shell command like `pytest tests/` or `python -m pytest`.
- `pytest` may still appear as a checker name in `qa_config.json` examples/context.
- No other prompt files are changed in this story.

## Developer Targets (exactly, no more / no less)

- `agent/developer.md` — replace direct `pytest` run instructions with `qa_compress.sh`
  description. Update the relevant section's prose. No path hardcoded.
- `agent/qa-manager.md` — same replacement.
- `tests/test_prompt_no_direct_pytest.py` — new test file: asserts that `agent/developer.md`
  and `agent/qa-manager.md` do not contain `pytest tests` or `python -m pytest` as shell
  commands (regex: `^\s*(python -m pytest|pytest\s+tests)` in non-code-block lines).

## Acceptance criteria (checked by qa-manager)

- `agent/developer.md` contains no `pytest tests/` or `python -m pytest` as a runnable command.
- `agent/qa-manager.md` same.
- Both files describe `qa_compress.sh` as the test runner.
- All tests pass.

## Test criteria (must exist BEFORE implementation)

- `tests/test_prompt_no_direct_pytest.py::test_developer_md_no_direct_pytest` — scan
  `agent/developer.md` for direct pytest invocations outside code-block context → assert none found.
- `tests/test_prompt_no_direct_pytest.py::test_qa_manager_md_no_direct_pytest` — same for
  `agent/qa-manager.md`.
- `tests/test_prompt_no_direct_pytest.py::test_qa_compress_mentioned_in_developer` — assert
  `agent/developer.md` contains the string `qa_compress.sh`.
- `tests/test_prompt_no_direct_pytest.py::test_qa_compress_mentioned_in_qa_manager` — assert
  `agent/qa-manager.md` contains the string `qa_compress.sh`.
