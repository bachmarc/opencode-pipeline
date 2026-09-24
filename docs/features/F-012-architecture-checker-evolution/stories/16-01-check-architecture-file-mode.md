# Story 16-01 — check_architecture.py: explicit file-list mode

Status: Planned
Feature: architecture-checker-evolution (F-012)

## Context / Purpose

`scripts/check_architecture.py` enforces the core-purity rule via a **directory**
argument (rglob) — that is the only invocation surface. Projects with root-level
layouts (no `src/core/` directory) cannot use the deterministic checker at all:
pointing it at the project root checks core AND adapter files together, and the
adapter legitimately imports framework modules (`appdaemon`, HA services) →
guaranteed FAIL. Concrete case: `intesis_modbus` (root files `klimasteuerung.py` =
pure core, `klima_geraet.py` = AppDaemon adapter). The project currently carries a
hand-rolled AST one-liner in its AGENTS.md acceptance criteria instead of the
framework tool — duplicated logic that will drift from the checker.

This story adds an explicit file-list mode so such projects run the SAME
deterministic checker as everyone else.

## Requirements

1. New CLI mode: `check_architecture.py --files <path> [<path> ...]` — check exactly
   the listed files, no directory rglob. Every listed file is checked against its
   language allowlist (per-suffix dispatch, identical to directory mode).
2. Old invocation `check_architecture.py <dir> [--allowlist <file>]` stays
   **byte-identical** in behavior and output (no new fields, no changed exit codes).
3. `--allowlist` works in both modes.
4. `--files` and a directory argument are mutually exclusive → usage FAIL with a
   clear error JSON.
5. Violation JSON format unchanged: `{"file", "import", "line"}`; `file` is the
   path as given (no relativization in file mode — there is no base directory).
6. PASS output schema: `{"result": "PASS", "files_checked": <N>}` where N = number
   of listed files actually checked (files with other suffixes contribute 0
   extraction but still count as encountered only if checked — same semantics as
   directory mode: only files matching CHECKED_GLOBS count).
7. A listed path that does not exist or is a directory → usage FAIL with error JSON
   (loud, never silently skipped — same discipline as unknown checker names in
   qa_compress.sh).
8. Docstring of the script documents both modes.

## Developer Targets (exactly, no more / no less)

- `scripts/check_architecture.py`:
  - Refactor the per-file check (extract → language allowlist → violation tuple)
    into a reusable unit (e.g. `check_file(file, allowlists, base_dir)`) —
    directory mode and file mode call it; NO duplicated per-language logic.
  - Add `--files` argument handling via argparse or explicit argv parsing
    consistent with the existing style.
  - File mode: for each listed file dispatch on suffix exactly like directory
    mode (`.py` AST, JS suffixes, `.rb`, `.java`; others → not checked, but a
    listed file with an unchecked suffix in file mode is a usage error per
    Requirement 7's spirit — decide + document: reject or skip; pick **reject**
    so typos fail loudly).
  - Update module docstring (two modes, mutual exclusion, exit codes).
- `tests/test_check_architecture_file_mode.py` (new — see test criteria).
- Do NOT touch `tests/test_check_scripts.py` or
  `tests/test_check_architecture_polyglot.py` (both must stay green unchanged —
  proof of backward compatibility).

## Acceptance criteria (checked by qa-manager)

- Directory-mode invocation unchanged: all existing architecture tests green
  WITHOUT modification (test_check_scripts.py, test_check_architecture_polyglot.py).
- `--files core.py adapter.py` with `core.py` importing `requests` → FAIL, violation
  lists `core.py`, `requests`, line; `adapter.py` not reported (it IS in the list —
  only checked files' violations appear; adapter's own imports are irrelevant since
  the operator lists core files only).
- `--files klimasteuerung.py` on a file importing only stdlib → PASS,
  `files_checked: 1`.
- `--files a.py b.js` → both checked (per-suffix dispatch), violations from either
  reported.
- `--allowlist` unlocks a module in file mode.
- `--files` + directory positional together → usage FAIL (error JSON, exit 1).
- `--files missing.py` → usage FAIL (error JSON), not silent skip.
- `py_compile` clean; no model/provider names; JSON output schema unchanged.

## Test criteria (must exist BEFORE implementation)

`tests/test_check_architecture_file_mode.py` — run script via subprocess against
tmp_path fixtures:

- `test_file_mode_python_stdlib_pass` — `--files core.py` with
  `import json; from pathlib import Path` → PASS, `files_checked: 1`.
- `test_file_mode_python_forbidden` — `--files core.py` with
  `import requests` → FAIL, violation contains `requests`, `core.py`, line number.
- `test_file_mode_multiple_languages` — `--files a.py b.js` where `a.py` is clean
  and `b.js` has `import axios from 'axios'` → FAIL, exactly one violation naming
  `b.js`/`axios`; `files_checked: 2`.
- `test_file_mode_relative_js_allowed` — `--files board.js` with
  `import { x } from './helper.js'` → PASS.
- `test_file_mode_allowlist` — `--files api.py` with `import mylib` +
  `--allowlist al.txt` containing `mylib` → PASS.
- `test_file_mode_rejects_missing_file` — `--files nope.py` → FAIL, error JSON
  mentions `nope.py`.
- `test_file_mode_rejects_directory_argument` — `--files somedir` (a directory) →
  FAIL error JSON.
- `test_mutual_exclusion_dir_and_files` — directory positional + `--files` →
  FAIL error JSON mentioning usage.
- `test_directory_mode_unchanged` — legacy invocation `<dir>` on a clean dir →
  PASS with `files_checked` (guards byte-identity of old mode; same fixture as
  polyglot tests uses).
- `test_file_mode_adapter_not_flagged` — `--files adapter.py` where adapter.py
  imports `appdaemon` and is NOT allowlisted but is deliberately not in the
  checked list → PASS (only listed files checked; documented semantics: the
  operator's responsibility is listing core files, same as pointing directory
  mode at src/core/).