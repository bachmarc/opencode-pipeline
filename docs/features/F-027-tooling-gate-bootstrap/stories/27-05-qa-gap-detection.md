# Story 27-05 — QA Gap Detection: analyze_project.py + provision_structure.py

Status: Planned
Feature: Tooling-Gate Bootstrap (F-027)

## Codebase Snapshot

- `scripts/analyze_project.py` — `detect_test_command()` (line 20) returns one checker name.
  `analyze_project()` (line 82) returns `qa_checker` as single string. Full file ~200 lines.
- `scripts/provision_structure.py` — `provision_structure()` writes `qa_config.json` with
  single checker (line ~70 area). Stack-to-checker mapping dict (line ~55). Full file ~200 lines.
- `tests/test_analyze_project.py` — existing tests for analyze_project.py.
- `tests/test_provision_structure.py` — existing tests for provision_structure.py.
- `command/new-project.md` — references `provision_structure.py` for bootstrapping.
- `skills/migrate-project.md` (if exists) — Phase 4 calls `provision_structure.py`.

## Context / Purpose

Today `analyze_project.py` detects ONE test checker (e.g. `jest`) and
`provision_structure.py` writes `{"checkers": ["jest"]}`. The full tooling stack
(lint, typecheck, format, audit) is never written — leaving projects with an
incomplete `qa_config.json` that silently skips all quality gates.

After this story, both scripts are stack-aware for the complete checker set:

| Stack | Checkers written to qa_config.json |
|---|---|
| javascript/typescript | `["jest", "eslint", "tsc", "prettier", "npm-audit"]` |
| python | `["pytest", "mypy", "ruff"]` |
| ruby | `["rspec", "rubocop"]` |
| java (gradle) | `["gradle", "checkstyle"]` |
| java (maven) | `["maven", "checkstyle"]` |
| json/yaml config | `["json", "yaml"]` |
| unknown | `["pytest"]` + Architect warned to research and create bootstrap story |

For unknown stacks: `analyze_project.py` sets a flag `"qa_bootstrap_needed": true`
in its output. `provision_structure.py` writes a placeholder `qa_config.json` with
`{"checkers": ["pytest"], "_bootstrap_needed": true, "_reason": "unknown stack — architect must research test tooling and update qa_config.json"}`.
This is NOT the Architect doing a websearch automatically — that's a separate manual step.
The flag is a visible signal in the onboarding output that the Architect must act.

## Requirements

1. `analyze_project.py`: Change `detect_test_command()` to return a **list** of checker names
   (not a single string). The stack-to-checkers mapping returns the full set per stack.
   The returned dict key changes from `"qa_checker": str` to `"qa_checkers": list[str]`.
   Backward-compat: if callers pass `analysis["qa_checker"]`, they'll get a KeyError — all
   callers must be updated (only `provision_structure.py` uses this field).

2. `provision_structure.py`: Update to read `analysis["qa_checkers"]` (list) instead of
   `analysis["qa_checker"]` (string). Write `{"checkers": [<all checkers>]}` to `qa_config.json`.
   For unknown stack: write `{"checkers": ["pytest"], "_bootstrap_needed": true, "_reason": "..."}`.

3. `provision_structure.py`: The `qa_checker` parameter (single string) in
   `provision_structure()` function signature is updated to `qa_checkers` (list of strings).
   Any existing callers in tests must be updated.

4. Both scripts update their docstrings to document the new list return type.

5. `analyze_project.py` output for TypeScript project (has `package.json`):
   `"qa_checkers": ["jest", "eslint", "tsc", "prettier", "npm-audit"]`

6. TypeScript detection: If `package.json` exists AND (`tsconfig.json` exists OR
   any `.ts` file exists in root or `src/`), treat as TypeScript → include `tsc`.
   Plain JavaScript (no TS markers): `["jest", "eslint", "prettier", "npm-audit"]` (no `tsc`).

## Developer Targets (exactly, no more / no less)

- `scripts/analyze_project.py`:
  - Rename `detect_test_command()` to `detect_qa_checkers()`, return type `-> tuple[list[str], str]`
    (checkers list, test_command string — keep test_command for backward compat of report format).
  - Add TypeScript detection logic (tsconfig.json or .ts files → add "tsc").
  - Update `analyze_project()`: use `detect_qa_checkers()`, return `"qa_checkers": [...]` (list).
    Keep `"test_command"` in output. Remove `"qa_checker"` key (breaking change — documented).
  - Update module docstring.

- `scripts/provision_structure.py`:
  - Update `provision_structure()` signature: `qa_checkers: list[str] = []` (was `qa_checker: str = ""`).
  - Update `qa_config.json` write logic to use the list.
  - Add `_bootstrap_needed` flag for unknown stack.
  - Update all internal references to `qa_checker` → `qa_checkers`.
  - Update module docstring.

- `tests/test_analyze_project.py`: Update existing tests that check `"qa_checker"` key
  → check `"qa_checkers"` (list). Add new tests:
  - `test_typescript_project_gets_tsc_checker` — project with tsconfig.json → `"tsc"` in checkers.
  - `test_javascript_project_no_tsc` — package.json, no tsconfig.json, no .ts files → no `"tsc"`.
  - `test_python_project_gets_full_checker_set` — pytest + mypy + ruff.
  - `test_ruby_project_gets_full_checker_set` — rspec + rubocop.
  - `test_unknown_stack_has_bootstrap_flag` — `"qa_bootstrap_needed": true` in output.

- `tests/test_provision_structure.py`: Update existing tests for new `qa_checkers` param.
  Add:
  - `test_provision_writes_full_ts_checkers` — JS/TS project → qa_config.json has all 5 checkers.
  - `test_provision_unknown_stack_writes_bootstrap_flag` — unknown stack → `_bootstrap_needed: true`.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `analyze_project.py` returns `"qa_checkers"` as list (not `"qa_checker"` as string).
- TypeScript detection works: tsconfig.json or `.ts` files → `"tsc"` in checkers list.
- `provision_structure.py` writes complete checker list to `qa_config.json`.
- Unknown stack writes `_bootstrap_needed: true` in `qa_config.json`.
- All new tests pass. All existing tests updated and passing.
- No other scripts broken (check `command/new-project.md` and migrate skill for references).

## Tooling Gates (mandatory — QA checks ALL of these)

- [ ] Tests green (`pytest`)
- [ ] Lint clean — N/A
- [ ] Typecheck clean — N/A
- [ ] Format check clean — N/A
- [ ] Audit clean — N/A

## Test criteria (must exist BEFORE implementation)

- `test_typescript_project_gets_tsc_checker` — creates tmpdir with `package.json` + `tsconfig.json`, runs `analyze_project()`, asserts `"tsc"` in `qa_checkers`. Protects: TypeScript detection not silently dropped.
- `test_javascript_project_no_tsc` — tmpdir with only `package.json`, no tsconfig/ts files → `"tsc"` NOT in `qa_checkers`. Protects: plain JS doesn't get a typecheck it can't run.
- `test_python_project_gets_full_checker_set` — tmpdir with `requirements.txt` → `qa_checkers` == `["pytest", "mypy", "ruff"]`. Protects: Python tooling stack complete.
- `test_ruby_project_gets_full_checker_set` — tmpdir with `Gemfile` → `["rspec", "rubocop"]`.
- `test_unknown_stack_has_bootstrap_flag` — empty tmpdir → `"qa_bootstrap_needed": true`.
- `test_provision_writes_full_ts_checkers` — provision with TS checkers list → qa_config.json contains all 5 checker names. Protects: provision actually writes the complete list.
- `test_provision_unknown_stack_writes_bootstrap_flag` — provision with unknown stack → qa_config.json has `_bootstrap_needed`.
