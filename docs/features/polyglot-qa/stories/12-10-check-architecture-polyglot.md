# Story 12-10 — check_architecture.py: polyglot import checking

Status: Planned
Feature: polyglot-qa (F-008)

## Context / Purpose

`scripts/check_architecture.py` enforces the core purity rule ("`src/core/` has
zero imports from framework/IO") — but it parses only Python files (AST). In a
Ruby/JS/Java project the automated architecture check silently checks nothing,
leaving the core/adapter separation to manual QA eyeballing. The QA checklist
(point 3) demands the check for every language; the tool must be able to deliver
it. This closes the "manual-only for non-Python" gap of the polyglot QA gate.

## Requirements

- `check_architecture.py` checks import statements per language, detected by
  file suffix, in the given directory (recursively):
  - `.py` — unchanged Python AST path, existing behavior byte-identical.
  - `.js`, `.ts`, `.jsx`, `.tsx` — regex-based: bare-specifier imports from
    `import ... from 'mod'`, side-effect `import 'mod'`, `require('mod')`,
    dynamic `import('mod')`, and re-exports (`export ... from 'mod'`).
    Relative imports (`./`, `../`) are project-internal → ALWAYS allowed
    (core may call core). Non-relative modules are checked against the
    Node-builtin allowlist (fs, path, os, http, url, crypto, util, events,
    stream, buffer, zlib, assert, net, tls, readline, string_decoder, worker_threads, …).
  - `.rb` — regex: `require 'x'` / `require "x"` checked against a Ruby-stdlib
    set (json, yaml, set, time, date, digest, socket, thread, singleton,
    forwardable, pathname, tempfile, fileutils, optparse, ostruct, logger, uri,
    net/http, base64, csv, …). `require_relative` is project-internal → ALWAYS
    allowed.
  - `.java` — regex: `import [static] <pkg>.<Class>;` — allowed prefixes
    `java.`, `javax.`, `jakarta.` (platform); everything else (e.g.
    `org.springframework`, `com.google`) is forbidden unless allowlisted.
- Custom `--allowlist` file continues to work for ALL languages (one module
  name per line, applied to the checked top-level module/package).
- Default allowlists per language are hard-coded constants in the script
  (deterministic, same pattern as the existing Python common-stdlib set).
- Violation JSON format unchanged: `{file, import, line}` — no new fields
  (existing pinned tests stay green).
- PASS output: `{"result": "PASS", "files_checked": <N>}` where N counts all
  checked files across languages.
- Regex-based extraction does NOT validate syntax — it only finds import
  statements (documented simplification; unparseable files are skipped, as
  with Python today).

## Developer Targets (exactly, no more / no less)

- Rework `scripts/check_architecture.py`:
  - Add constants `NODE_BUILTINS`, `RUBY_STDLIB`, `JAVA_ALLOWED_PREFIXES`
    (with the entries from Requirements).
  - `extract_js_imports(file_path) -> list[tuple[str, int]]` — regex
    `r"(?:from\s+|require\(\s*|import\(\s*|import\s+)['\"]([^'\"]+)['\"]"`;
    skip matches starting with `./` or `../`; return (module, line).
  - `extract_ruby_imports(file_path)` — regex
    `r"^\s*require\s+['\"]([^'\"]+)['\"]"`; `require_relative` never matched
    (different keyword), return (module, line).
  - `extract_java_imports(file_path)` — regex
    `r"^\s*import\s+(?:static\s+)?([\w.]+)\s*;"`; check the first package
    segment against allowed prefixes; return (package, line).
  - `extract_imports(file_path)` dispatches on suffix: `.py` → existing AST
    function (unchanged), JS suffixes/rb/java → new regex functions, other
    suffixes → `[]`.
  - `check_architecture()`: rglob over `*.py`, `*.js`, `*.ts`, `*.jsx`,
    `*.tsx`, `*.rb`, `*.java`; per-language allowlist union with custom
    allowlist; Python files use the existing stdlib+custom allowlist
    (byte-identical semantics).
  - Update module docstring (multi-language contract).
- Add `tests/test_check_architecture_polyglot.py` (see test criteria).
- Do NOT touch `tests/test_check_scripts.py` (existing architecture tests
  there must stay green unchanged — proof of Python compatibility).

## Acceptance criteria (checked by qa-manager)

- All existing Python behavior identical: `tests/test_check_scripts.py`
  architecture tests green WITHOUT modification.
- JS core importing `axios` → FAIL with `import: axios` + file + line;
  importing `path`/`fs` → PASS; importing `./helper` → PASS (relative).
- Ruby core with `require 'json'` → PASS; `require 'sinatra'` → FAIL;
  `require_relative 'board'` → PASS.
- Java core with `import java.util.List;` → PASS;
  `import org.springframework.stereotype.Service;` → FAIL.
- Mixed core dir (`.py` + `.js` + `.rb` + `.java` files in one run) → all
  checked; single violation → overall FAIL listing exactly that file.
- Custom allowlist unlocks a non-stdlib import for any language
  (e.g. `mylib` in JS).
- `py_compile` clean; JSON output schema unchanged; no model/provider names.

## Test criteria (must exist BEFORE implementation)

`tests/test_check_architecture_polyglot.py` — tmp_path src/core dirs, run
script via subprocess:

- `test_js_clean` — `core/board.js` with `import path from 'path'` and
  `import { helper } from './helper.js'` → PASS, `files_checked: 1`.
- `test_js_forbidden` — `core/api.js` with `import axios from 'axios'` →
  FAIL, violation contains `axios` and the file name.
- `test_js_require_form` — `core/old.js` with `const fs = require('fs')`
  (PASS) and `const db = require('mongoose')` (FAIL, `mongoose`).
- `test_ts_file_checked` — `core/board.ts` with
  `import { Board } from './types'` + `import http from 'http'` → PASS.
- `test_ruby_clean_and_relative` — `core/board.rb` with
  `require 'json'` + `require_relative 'cell'` → PASS.
- `test_ruby_forbidden` — `core/app.rb` with `require 'sinatra'` → FAIL,
  violation contains `sinatra`.
- `test_java_clean` — `core/Board.java` with `import java.util.List;` →
  PASS.
- `test_java_forbidden` — `core/Service.java` with
  `import org.springframework.stereotype.Service;` → FAIL, contains
  `org.springframework`.
- `test_mixed_language_dir` — `board.py` (clean) + `api.js` (axios) in one
  dir → FAIL with exactly the `api.js` violation; `files_checked: 2`.
- `test_allowlist_unlocks_js_module` — `import axios from 'axios'` +
  allowlist file containing `axios` → PASS.