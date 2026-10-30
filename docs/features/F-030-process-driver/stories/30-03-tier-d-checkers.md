# Story 30-03 — Tier D process checkers: worktree discipline + metadata affects

Status: Planned
Feature: Process Driver (F-030)

## Codebase Snapshot

- `scripts/qa_compress.py` — flat checker registry; checkers are functions
  returning `tuple[str, int]` (summary, exit code), ~24 existing checkers
  (`pytest_check` line ~82 … `black_check` line ~1051). Registry dict
  `CHECKERS` at line ~1095; `_load_config()` ~line 1116 reads
  `qa_config.json`; `_validate_configured_checkers()` ~line 1153; `main()`
  ~line 1259. New process checkers plug into this pattern.
- `scripts/worktree_setup.py` — worktree naming convention
  `.worktrees/<story-id>-<slug>` and branch `feature/<story-id>-<slug>`.
- `scripts/prepare_commit_metadata.py` — commit metadata format
  `symbols: ... | breaks: ... | affects: ... | tests: ...` (the strings this
  checker validates).
- `scripts/merge_if_passed.py` — reads `qa-state/*.json` verdicts; the checker
  here is independent of merge logic, it only inspects git + commit messages.
- Existing checker test pattern: `tests/test_qa_checkers_python_lint.py` and
  `tests/test_qa_checkers_rspec_jest.py` — each installs a STUB runner binary
  and asserts summary lines + overall PASS/FAIL behavior. The new checkers
  call `git` (available in test env) against a fixture repo instead of a stub
  binary.

## Context / Purpose

The qa-manager repeatedly found two classes of problems that are actually
mechanical: (1) the developer worked OUTSIDE the story worktree (wrong cwd or
commits from other worktrees), and (2) commit metadata (`affects:`/`symbols:`)
did not match the real change set, hiding regressions in dependent code. Both
checks cost the LLM reading time in every QA round when a script can decide
them in milliseconds. This story adds two Tier D checkers to the
`qa_compress.py` registry so they run exactly like the tooling gates — zero
token cost, machine-readable verdicts.

## Requirements

1. New checker `worktree_discipline()` in `scripts/qa_compress.py`:
   - Input: commit/HEAD context is derived from the repo it runs in; the
     required worktree path and branch come from `qa_config.json`
     (`process_checker.story_id` + optional `process_checker.worktree_root`).
   - Rule: for the story branch `feature/<story-id>-*`, the tip commit must be
     reachable from a worktree registered at
     `.worktrees/<story-id>-*` in `git worktree list` output.
   - PASS output: `{"result": "PASS", "branch": ..., "worktree": ...}`;
     FAIL: reason string (branch missing from worktree list / no worktree
     registered for story / branch tip not from expected worktree).
2. New checker `metadata_affects()` in `scripts/qa_compress.py`:
   - Reads the LAST commit's message, extracts `symbols:`, `affects:`,
     `breaks:`, `tests:` segments (pipe-separated key-value convention).
   - Rule: every path listed in `affects:` must exist in the repo; the
     changed files in the commit (via `git show --name-only`) that live in
     `src/`/`tests/` must appear in `symbols:`/`affects:` declarations OR the
     commit must be docs/planning-only.
   - PASS: `{"result": "PASS", "checks": <n>}`; FAIL lists every inconsistent
     path.
3. Both checkers are registry-selected via `qa_config.json` (names
   `worktree_discipline`, `metadata_affects`) and are OFF by default (not in
   the default config selection — projects opt in per profile, aligning with
   process.json `test_strategy`).
4. `qa_config.json` schema extension in `_validate_configured_checkers()` /
   `_load_config()`: optional `process_checker` object with `story_id` and
   `worktree_root` (string, default `.worktrees`). Unknown process_checker
   keys → validation error like checkers.
5. Docs: `qa_compress.py` module docstring gains one paragraph listing the two
   process checkers and their config keys.

## Developer Targets (exactly, no more / no less)

- `scripts/qa_compress.py`: add the two check functions, register them in
  `CHECKERS`, extend `_load_config`/`_validate_configured_checkers` for the
  `process_checker` block, extend module docstring.
- `tests/test_qa_checkers_process.py`: new test file using a real temp git
  repo (`git init`, commits via subprocess `git`) covering both checkers.
- Nothing else — do NOT touch merge logic, agent prompts, or
  `worktree_setup.py`.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `qa_compress.py` with a config selecting only
  `["worktree_discipline"]` on a clean fixture repo prints
  `## worktree_discipline (exit: 0)` in its summary and overall PASS.
- The two new checkers do NOT run when not selected in `qa_config.json`
  (backwards compatibility with all existing project configs).
- `metadata_affects` catch demonstration: a commit whose diff touches
  `src/foo.py` but declares `affects: nothing` fails with `src/foo.py` named.

## Test criteria (must exist BEFORE implementation)

- `tests/test_qa_checkers_process.py::test_worktree_discipline_pass` — story
  branch exists, worktree registered from `.worktrees/<id>-x` → exit 0.
- `tests/test_qa_checkers_process.py::test_worktree_discipline_stale` — branch
  exists, NO worktree registered → exit 1, message mentions worktree.
- `tests/test_qa_checkers_process.py::test_worktree_discipline_wrong_dir` —
  worktree registered under unexpected path (not `.worktrees/<id>-*`) → exit
  1.
- `tests/test_qa_checkers_process.py::test_metadata_pass` — well-formed
  metadata commit (symbols/affects match diff) → exit 0.
- `tests/test_qa_checkers_process.py::test_metadata_missing_affects` — code
  change without affects/symbols declaration → exit 1, missing path listed.
- `tests/test_qa_checkers_process.py::test_metadata_docs_only_commit` — docs
  commit changes no code paths → PASS without declarations.
- `tests/test_qa_checkers_process.py::test_not_selected_checkers_dont_run` —
  config with only `["pytest"]` runs as before (registry unchanged).

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black)
