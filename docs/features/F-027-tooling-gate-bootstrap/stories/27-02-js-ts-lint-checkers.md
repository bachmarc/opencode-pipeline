# Story 27-02 — JS/TS Lint Checkers: eslint, tsc, prettier, npm-audit

Status: Planned
Feature: Tooling-Gate Bootstrap (F-027)

## Codebase Snapshot

- `scripts/qa_compress.py` — inline checker functions + CHECKERS registry dict (lines ~563–578).
  Existing pattern: `def jest_check() -> tuple[str, int]` (line 175), `"jest": jest_check` in CHECKERS.
  `_load_config()` reads `qa_config.json`, `_validate_configured_checkers()` rejects unknown names.
  Adding a checker = one function + one dict entry. No other files to touch.
- `scripts/qa_checkers/jest.py` — dead code (self-registration mechanism never used by qa_compress.py).
  New checkers go inline in `qa_compress.py` only — do NOT add to `qa_checkers/`.
- `tests/test_qa_checkers_jest.py` (or similar) — existing test pattern for checkers using fake binaries.
  Check which test files exist for jest/rspec to understand the fake-binary test pattern.

## Context / Purpose

`qa_compress.py` has no checkers for the JS/TS tooling stack. A project declaring
`{"checkers": ["jest", "eslint", "tsc", "prettier", "npm-audit"]}` would crash on the
four new names with "unknown checker". This story adds all four as inline checker
functions following the exact same pattern as existing checkers.

After this story, a TypeScript project can declare all its tooling gates in `qa_config.json`
and `qa_compress.py` will run all of them.

## Requirements

1. `eslint_check()` — runs ESLint. Invocation priority: `node_modules/.bin/eslint` first,
   then `npx eslint`, then `eslint` on PATH. Falls back to next if binary not found.
   If none found: `"eslint not found (checked: node_modules/.bin/eslint, npx, PATH)\n"`, exit 1.
   Compressed output: error count + first 20 error lines on failure. On success: `"eslint: 0 errors\n"`.

2. `tsc_check()` — runs TypeScript compiler check (`--noEmit`). Invocation:
   `node_modules/.bin/tsc --noEmit` first, then `npx tsc --noEmit`, then `tsc --noEmit`.
   Not found: `"tsc not found\n"`, exit 1.
   Compressed output: error count line + first 20 TS errors on failure. On success: `"tsc: 0 errors\n"`.

3. `prettier_check()` — runs Prettier in check mode. Invocation:
   `node_modules/.bin/prettier --check .` first, then `npx prettier --check .`.
   Not found: `"prettier not found\n"`, exit 1.
   Compressed output: list of unformatted files (max 20) on failure. On success: `"prettier: all files formatted\n"`.

4. `npm_audit_check()` — runs `npm audit --audit-level=high`. Requires `npm` on PATH.
   Not found: `"npm not found\n"`, exit 1.
   Compressed output: vulnerability count + severity summary on failure. On success: `"npm audit: 0 high/critical\n"`.
   Checker name in registry: `"npm-audit"` (hyphen, consistent with qa_config.json naming).

5. All four are registered in `CHECKERS` dict in `qa_compress.py`.

6. Local-first invocation: always try `node_modules/.bin/<tool>` before global. This enforces
   the "no global dependency" contract — projects must have tools as devDependencies.

## Developer Targets (exactly, no more / no less)

- `scripts/qa_compress.py`: Add four new checker functions inline, in this order after `jest_check()`:
  - `eslint_check() -> tuple[str, int]`
  - `tsc_check() -> tuple[str, int]`
  - `prettier_check() -> tuple[str, int]`
  - `npm_audit_check() -> tuple[str, int]`
  Add all four to `CHECKERS` dict: `"eslint": eslint_check`, `"tsc": tsc_check`,
  `"prettier": prettier_check`, `"npm-audit": npm_audit_check`.
  Update module docstring to list new checker names.

- `tests/test_qa_checkers_js_ts.py` (new file): Tests using fake binaries on PATH.
  See existing test pattern in `tests/test_qa_checkers_jest.py` or equivalent.
  Tests: success path, failure path (errors found), not-found path for each checker.
  12 tests minimum (3 per checker × 4 checkers).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `qa_compress.py` CHECKERS dict contains `"eslint"`, `"tsc"`, `"prettier"`, `"npm-audit"`.
- Each checker: tries `node_modules/.bin/<tool>` before PATH/npx.
- Each checker: returns clear error message and exit 1 when binary not found anywhere.
- Each checker: returns compressed summary (not raw log) on success and failure.
- All 12+ new tests pass.
- No existing tests broken (`pytest` still green).
- `qa_config.json: {"checkers": ["eslint"]}` no longer crashes with "unknown checker".

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root (this is the pipeline framework repo).

- [ ] Tests green (`pytest`)
- [ ] Lint clean — N/A (no lint checker configured in framework's own qa_config.json)
- [ ] Typecheck clean — N/A
- [ ] Format check clean — N/A
- [ ] Audit clean — N/A

## Test criteria (must exist BEFORE implementation)

- `test_eslint_check_success` — fake `eslint` binary exits 0 with "no problems" output → checker returns exit 0, output contains "0 errors". Protects: success path.
- `test_eslint_check_failure` — fake `eslint` exits 1 with 3 error lines → checker returns exit 1, compressed output contains error lines. Protects: failure path shows actual errors.
- `test_eslint_check_not_found` — no eslint anywhere → checker returns exit 1, message contains "not found". Protects: clear error instead of cryptic crash.
- `test_tsc_check_success` — fake `tsc --noEmit` exits 0 → exit 0, "0 errors".
- `test_tsc_check_failure` — fake `tsc` exits 1 with TS errors → exit 1, compressed TS errors.
- `test_tsc_check_not_found` — no tsc → exit 1, "not found".
- `test_prettier_check_success` — fake `prettier --check` exits 0 → exit 0, "all files formatted".
- `test_prettier_check_failure` — fake `prettier` exits 1 listing unformatted files → exit 1, file list.
- `test_prettier_check_not_found` — no prettier → exit 1, "not found".
- `test_npm_audit_check_success` — fake `npm audit` exits 0 → exit 0, "0 high/critical".
- `test_npm_audit_check_failure` — fake `npm` exits 1 with vulnerability count → exit 1, summary.
- `test_npm_audit_check_not_found` — no npm → exit 1, "not found".
