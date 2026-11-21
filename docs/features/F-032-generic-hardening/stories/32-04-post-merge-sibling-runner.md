# Story 32-04 — Post-merge suite gate: sibling-runner fallback for onboarded projects

Status: Planned
Feature: Generic Pipeline Hardening (F-032)

## Codebase Snapshot

- `scripts/merge_if_passed.py` — `run_post_merge_suite()` (~line 251): resolves the QA runner
  at line 283 via `root / "scripts" / "qa_compress.py"` only; lines 284-285: immediate SKIPPED
  if that path is absent. This is the only location that needs to change.
- `scripts/qa_compress.py` — the actual QA runner; lives in the same directory as
  `merge_if_passed.py` in both the framework dev-repo and the live-clone. The sibling path
  `Path(__file__).resolve().parent / "qa_compress.py"` resolves to this file from either clone.
- `scripts/provision_structure.py` — onboarding script; does NOT create `scripts/` or
  `qa_compress.py` in the project root. Confirmed by grep (zero matches for `qa_compress`).
- `tests/test_merge_if_passed.py` — 9 tests (6 pre-32-02 + 3 added by 32-02). The 3 post-merge
  tests (`test_post_merge_green_exit0`, `test_post_merge_red_exit3_note`,
  `test_post_merge_runner_missing_skipped`) all create the stub at
  `tmp_path / "scripts" / "qa_compress.py"` — they test the local-runner path (priority 1) and
  remain unchanged. New tests cover priority 2 (sibling) and priority 3 (neither).

## Context / Purpose

Story 32-02 added a post-merge main-health check: after every successful merge,
`merge_if_passed.py` runs the configured QA suite on main to catch regressions introduced
by the merge itself (e.g., two clean branches that conflict when combined).

The check was designed with a fail-open: if the runner script is missing, it emits
`"post_merge": {"suite": "SKIPPED"}` and exits 0 — missing tooling must not block merges.

However, the runner lookup was hardcoded to `<project-root>/scripts/qa_compress.py`. Onboarded
projects (migrated via `/migrate-project`) never have this file — `provision_structure.py`
creates the `.pipeline/` structure but does NOT copy or create the QA runner. The fail-open is
correct semantically, but the lookup is wrong: the runner exists (as the sibling
`scripts/qa_compress.py` in the framework itself), it just isn't found.

Result: for every onboarded project (confirmed: 4/4 intesis_modbus merges, all SKIPPED),
the post-merge gate never runs — silently, without any configuration change and without any
error. The invariant "no further stories on red main" has no deterministic enforcement for
onboarded projects.

**Fix:** a 3-priority resolution chain in `run_post_merge_suite()`:
1. `<project-root>/scripts/qa_compress.py` — local project runner (highest priority; a project
   can pin its own version by placing one here).
2. `Path(__file__).resolve().parent / "qa_compress.py"` — sibling of `merge_if_passed.py`;
   resolves correctly from both the framework dev-repo and the live-clone; no config needed.
3. Neither found → SKIPPED + documented reason (fail-open preserved for genuine tooling absence).

## Requirements

1. **3-priority runner resolution:** `run_post_merge_suite()` tries (1) local then (2) sibling
   before concluding (3) SKIPPED. Execution behavior (cwd, exit-code mapping, JSON contract)
   is unchanged once a runner is selected.
2. **Local runner priority is verifiable:** when BOTH a local runner AND the sibling exist,
   the local runner is selected (a project's pinned version wins over the framework default).
3. **Fail-open preserved:** when neither path exists, the function returns
   `{"suite": "SKIPPED", "reason": "..."}` and the caller exits 0. No new config keys required.
4. **Resolution extracted as a testable helper `_resolve_suite_script`:**
   `_resolve_suite_script(root: Path, _script_dir: Path | None = None) -> Path | None` —
   the `_script_dir` parameter defaults to `Path(__file__).resolve().parent` (the sibling
   directory) and is overridable in tests to avoid dependency on the live filesystem.
5. **No changes** to the QA-PASS check, the documenter-commit check, the merge sequence,
   or the exit-code contract (exit 0 / 1 / 2 / 3 semantics from Story 32-02 are unchanged).

## Developer Targets (exactly, no more / no less)

- `scripts/merge_if_passed.py`:
  - Add `_resolve_suite_script(root: Path, _script_dir: Path | None = None) -> Path | None`
    — tries local runner first, then sibling (`_script_dir / "qa_compress.py"`), returns
    `None` if neither found.
  - Replace lines 283–285 (the single `suite_script = …` + `if not … is_file(): return SKIPPED`
    block) with a call to `_resolve_suite_script(root)`; keep the SKIPPED return if result is `None`.
  - Update module docstring: replace the description of the hardcoded runner lookup with the
    3-priority chain (local → sibling → SKIPPED).
- `tests/test_merge_if_passed.py`:
  - `test_resolve_suite_script_local_wins` — unit test of `_resolve_suite_script`: both
    local (`_script_dir / "qa_compress.py"`) and local-project runner (`root / "scripts" / "qa_compress.py"`)
    exist → local project runner returned (priority 1 wins).
  - `test_resolve_suite_script_sibling_fallback` — unit test: no local project runner, sibling
    exists → sibling returned.
  - `test_resolve_suite_script_neither_skipped` — unit test: neither exists → `None` returned.
  - `test_post_merge_sibling_runner_integration` — subprocess integration test: mergeable repo
    fixture WITHOUT `scripts/qa_compress.py`; `qa_config.json` with `{"checkers": ["pytest"]}`;
    fake `pytest` binary on PATH; sibling stub written alongside a temporary copy of
    `merge_if_passed.py` (or use `_script_dir` override via monkeypatch of `__file__`) —
    runner resolves to sibling, suite runs, exit 0 and `post_merge.suite == "PASS"`.
    **Implementation note:** the subprocess integration path cannot use the `_script_dir`
    override directly; instead the test writes a stub as `<sibling_dir>/qa_compress.py`
    where `sibling_dir` is the REAL `scripts/` directory of the framework repo (since the
    real `scripts/qa_compress.py` already exists, writing the stub there would corrupt it —
    use a modified approach: copy `merge_if_passed.py` to a tmp scripts dir alongside a stub
    `qa_compress.py`, adjust PATH/cwd). **Simpler alternative the developer may choose:**
    make `_script_dir` injectable via an env-var `_MERGE_SCRIPT_DIR_OVERRIDE` (test-only,
    documented as such); this avoids file-system corruption risk entirely.
  - Update module docstring: note that tests import `_resolve_suite_script` directly for unit
    coverage.
- Update docstrings and module headers in every file you change — code documentation is the
  source of truth.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `_resolve_suite_script(root_without_local, _script_dir=dir_with_sibling)` returns the sibling path.
- `_resolve_suite_script(root_with_local, _script_dir=dir_with_sibling)` returns the local path (priority 1).
- `_resolve_suite_script(root_without_local, _script_dir=dir_without_sibling)` returns `None`.
- Subprocess integration: post-merge runs via sibling and returns `post_merge.suite == "PASS"` (exit 0).
- All 9 pre-existing `test_merge_if_passed.py` tests still pass (no regression to 32-02 work).
- Module docstring of `merge_if_passed.py` describes the 3-priority resolution chain.
- No config-schema change (`qa_config.json` format unchanged).

## Test criteria (must exist BEFORE implementation)

- `tests/test_merge_if_passed.py::test_resolve_suite_script_local_wins`
- `tests/test_merge_if_passed.py::test_resolve_suite_script_sibling_fallback`
- `tests/test_merge_if_passed.py::test_resolve_suite_script_neither_skipped`
- `tests/test_merge_if_passed.py::test_post_merge_sibling_runner_integration`

<!-- For lifecycle stories (multi-step lifecycles: start/stop, publish/subscribe,
     join/leave, transactional sequences) the architect adds this section and
     fills it. Applicability is the architect's judgment — there is no
     trigger-word automation. This comment persists verbatim into generated
     stories (harmless, no plan_check impact); for lifecycle stories, uncomment
     the section below:

## Ordering & Recovery Invariants (mandatory for lifecycle stories)

- <Ordering: which step must never run before/after which other step>
- <Intermediate states: what is visible/consistent while a transition runs>
- <Abort/recovery: stop vs rollback vs resume semantics mid-flight>
- <Idempotency: repeat/reconnect/re-delivery of the same step is safe>

-->

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest per `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black)
