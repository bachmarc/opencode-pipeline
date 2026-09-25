# Story 20-03 — qa_compress.py as Mandatory Sole Test Entry Point in Prompts

Status: Planned
Feature: script-portability-fixes (F-020)

## Context / Purpose

Story 19-01 replaced `qa_compress.sh` with `qa_compress.py` (Python). However, `agent/developer.md`
and `agent/qa-manager.md` still reference `qa_compress.sh`. As a result, QA-Manager agents fall
back to running `pytest` directly — which silently skips all non-pytest checkers (Java, HTML,
YAML, etc.) configured in `qa_config.json`.

Story 17-04 previously made `qa_compress.sh` the sole entry point in prompts, but that fix is now
stale after the Python migration. Additionally, the `qa-manager.md` wording is too weak
(`/ qa_compress.sh` as an alternative) — it must be a hard prohibition.

## Requirements

- `agent/developer.md`: replace `qa_compress.sh` with `qa_compress.py`. The description must
  make clear this is the **only** way to run tests — no direct `pytest` or `python -m pytest`.
- `agent/qa-manager.md`: replace `qa_compress.sh` with `qa_compress.py`. Add explicit prohibition:
  "Never run `pytest` directly — always use `qa_compress.py`." The wording must be unambiguous.
- Neither file contains `qa_compress.sh` after this change.
- Neither file contains a runnable `pytest tests/` or `python -m pytest` command outside of
  `qa_config.json` examples.
- `pytest` may still appear as a checker name in `qa_config.json` context/examples.

## Developer Targets (exactly, no more / no less)

- `agent/developer.md`:
  - Replace `qa_compress.sh` → `qa_compress.py` in the test-run instruction (step 7).
  - Update docstring/header if present.
- `agent/qa-manager.md`:
  - Replace `qa_compress.sh` → `qa_compress.py` in checklist item 2.
  - Rewrite the sentence to make `qa_compress.py` the **mandatory sole entry point** — add
    explicit prohibition of direct `pytest` invocation.
  - Update docstring/header if present.
- `tests/test_prompt_no_direct_pytest.py` (existing file from story 17-04):
  - Update assertions: check for `qa_compress.py` (not `.sh`) in both prompt files.
  - Existing tests `test_developer_md_no_direct_pytest` and `test_qa_manager_md_no_direct_pytest`
    must still pass (no direct pytest commands).
  - Add: `test_developer_md_references_qa_compress_py` — assert `agent/developer.md` contains
    `qa_compress.py`.
  - Add: `test_qa_manager_md_references_qa_compress_py` — assert `agent/qa-manager.md` contains
    `qa_compress.py`.
  - Add: `test_no_qa_compress_sh_in_prompts` — assert neither `agent/developer.md` nor
    `agent/qa-manager.md` contains `qa_compress.sh`.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `agent/developer.md` contains `qa_compress.py`, not `qa_compress.sh`.
- `agent/qa-manager.md` contains `qa_compress.py`, not `qa_compress.sh`.
- `agent/qa-manager.md` contains an explicit prohibition of direct `pytest` invocation.
- All tests pass (`qa_compress.py`).

## Test criteria (must exist BEFORE implementation)

- `tests/test_prompt_no_direct_pytest.py::test_developer_md_references_qa_compress_py` — assert
  `agent/developer.md` contains the string `qa_compress.py`.
- `tests/test_prompt_no_direct_pytest.py::test_qa_manager_md_references_qa_compress_py` — assert
  `agent/qa-manager.md` contains the string `qa_compress.py`.
- `tests/test_prompt_no_direct_pytest.py::test_no_qa_compress_sh_in_prompts` — assert neither
  `agent/developer.md` nor `agent/qa-manager.md` contains `qa_compress.sh`.
- Existing tests `test_developer_md_no_direct_pytest` and `test_qa_manager_md_no_direct_pytest`
  continue to pass.
