# Story 12-05 — Checker plugin: HTML

Status: Done (QA PASS, 374ad8f)
Feature: polyglot-qa (F-008)

## Requirement: simple syntax check only

The user explicitly decided: a simple HTML checker is enough — no accessibility
audits, no link checking, no JS execution, no CSS lint. If a browser-level check
is ever needed it comes as a jest-based story in a project, not as a framework
checker.

## Context / Purpose

HTML files are part of the user's daily business. The QA gate should catch
basic structural syntax errors (unclosed/unclosed-mismatched essential tags)
deterministically before merge. "Simple" is the contract: what this checker
must do and nothing more.

## Requirements

- Checker `html`: validates all `*.html` files in cwd with a simple
  structural check:
  - File must parse via Python stdlib `html.parser.HTMLParser` without
    raising (strict structural errors).
  - Balanced essential tags check: for the void-tag whitelist
    (`br`, `hr`, `img`, `input`, `meta`, `link`, `area`, `base`, `col`,
    `embed`, `source`, `track`, `wbr`), opening tags do NOT need closing.
    For all other tags, every open tag must be closed with a matching close
    tag in correct order (stack discipline). `<p>` may be closed implicitly
    by a following block element ONLY if that is how HTML defines it —
    for simplicity: `p` is added to the no-stack-check set (implicit close
    is legal in HTML), documented as a known simplification.
  - Each invalid file → one line `INVALID <path> (<reason>)` under
    `## failed_files`, ≤20.
  - Valid repo → summary `N files checked, 0 invalid`, exit 0.
- Same exclusion dirs as 12-04 (`.git`, `.pipeline`, `.worktrees`,
  `node_modules`, `__pycache__`, `.pytest_cache`, `dist`, `build`).
- Stdlib only — no new dependencies (html.parser is stdlib).
- Plugin contract as in 12-02..12-04: self-registering file
  `scripts/qa_checkers/html.sh`, no shared-file edits.

## Developer Targets (exactly, no more / no less)

- `scripts/qa_checkers/html.sh`: `html_check()` — walks `**/*.html` under cwd
  (excluding listed dirs); validates via a python3 one-liner embedding a
  small `HTMLParser` subclass: void tags ignored, every other open tag
  pushed on a stack, close tag must match top-of-stack (pop), unclosed
  remaining stack or mismatch → invalid (with reason: `unclosed <tag>` /
  `mismatch: expected </A> got </B>`); `p` excluded from stack checking
  (documented simplification); output identical format to 12-04
  (`N files checked, M invalid`, `## failed_files` + `INVALID <path>
  (<reason>)`, ≤20, exit 1 on any invalid); `register_check html html_check`.
- `tests/test_qa_checker_html.py` (see test criteria).

## Acceptance criteria (checked by qa-manager)

- Valid HTML file (doctype, head/body, divs) → PASS, summary
  `1 files checked, 0 invalid`.
- Missing `</div>` → FAIL, `INVALID <path> (unclosed div)` listed.
- Mismatched close tag (`<div>...</span>`) → FAIL, reason contains
  `mismatch`.
- Void tags without closing (`<br>`, `<img src="x">`) → PASS (no false
  positive).
- `node_modules/` content ignored → PASS despite broken HTML inside.
- Existing checkers unchanged; 12-01..12-04 tests green; `bash -n` clean;
  no model/provider names.

## Test criteria (must exist BEFORE implementation)

`tests/test_qa_checker_html.py` — tmp_path project roots:

- `test_html_pass` — config `["html"]`; create `index.html` with
  `<!DOCTYPE html><html><head></head><body><div>hi</div></body></html>`
  → overall PASS.
- `test_html_unclosed` — `<div>` without close → FAIL, output contains
  `unclosed div`.
- `test_html_mismatch` — `<div>text</span>` → FAIL, output contains
  `mismatch`.
- `test_html_void_tags_ok` — `<p>text<br><img src="x.png">` (p implicit,
  br/img void) → PASS.
- `test_html_excludes_dirs` — broken HTML in `node_modules/x.html` →
  PASS (excluded).