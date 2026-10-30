# Story 29-01: `worktree_cleanup.py` + Session-Recovery Staleness Check

Feature: F-029 worktree-hygiene

## Context / Purpose

`worktree_setup.py` creates a worktree per story; nothing ever removes them.
The VirtOffice incident (F-029 Context) showed the accumulation cost: every
git-registered stale worktree spawns a Playwright-MCP server + watchers at
every opencode server start. This story builds the deterministic, zero-token
countermeasure and makes staleness visible at every session start.

**Feature:** `docs/features/F-029-worktree-hygiene/feature.md`

**Scope boundary:** Python script + session-recovery addition + tests. No
changes to `worktree_setup.py` (creation flow stays), no opencode record-store
manipulation (out of scope, upstream limitation), no merge-flow integration
(follow-up story if wanted).

## Requirements

### R1 — `scripts/worktree_cleanup.py` (deterministic, stdlib-only)

1. Enumerate worktrees via `git worktree list --porcelain`, exclude the main
   checkout (the one whose path equals the repo root / the branch considered
   primary).
2. Classify each worktree:
   - `branch`: checked-out branch name (or `detached`)
   - `merged`: branch fully merged into the default branch (`git branch
     --merged <default>`) — detached HEADs count as merged iff their commit
     is an ancestor of the default branch tip
   - `dirty`: `git -C <worktree> status --porcelain` non-empty
3. **Dry run (default):** print a plan table (path, branch, merged, dirty,
   action) + summary counts; exit 0 when nothing to do, exit 1 when actions
   are available (so it is CI/cron-usable).
4. **`--apply`:** execute the plan:
   - merged + clean → `git worktree remove <path>`
   - merged + dirty → labeled stash first (`git -C <path> stash push -m
     "worktree-cleanup: <branch>"`), then remove
   - NOT merged → NEVER removed, listed as "keep (unmerged)" in plan and run
   - afterwards: `git worktree prune`
5. **`--purge-folders`:** scan the configured worktree parent dir (default
   `.worktrees/`, overridable via `--worktree-dir`) for directories without a
   git registration: folders WITHOUT a `.git` link file → delete; folders
   WITH a dead `.git` link file → refuse + report for manual review (their
   dirtiness cannot be assessed via git). Never the default; requires
   `--apply` too.
6. Windows (PowerShell) + bash compatible; no shell-specific parsing; all
   git calls via `subprocess` with explicit args (no shell=True), matching
   the portability rules that F-020 established.

### R2 — `session_recovery.py` staleness summary

Read-only addition to the existing scan output: one block reporting
registered non-main worktree count, of which merged+clean (auto-removable)
count, plus the hint line: `hint: python scripts/worktree_cleanup.py (dry-run)
to see the cleanup plan`. No behavior change to the rest of the script.

### R3 — Tests (`tests/test_worktree_cleanup.py`)

pytest against a temporary fixture repo (created in tmp via `git init` +
commits + `git worktree add`):
1. classification: merged+clean, merged+dirty, unmerged worktrees classified
   correctly
2. dry-run: correct plan table, exit 0 with no stale worktrees, exit 1 with
3. `--apply`: merged+clean removed; merged+dirty stashed (assert stash list
   entry) then removed; unmerged untouched
4. `git worktree prune` called
5. `--purge-folders`: `.git`-less folder deleted, dead-`.git` folder refused
6. R2: session_recovery output includes the staleness block (assert on the
   formatting function, not the full script run)

## Acceptance Criteria

1. ✅ Dry-run on a repo with zero non-main worktrees prints counts and exits 0.
2. ✅ `--apply` on the fixture: exactly the merged worktrees removed, unmerged
   survivor intact, dirty one recoverable via the labeled stash.
3. ✅ Unregistered `.git`-less folders purged only with `--purge-folders
   --apply`; dead-`.git` folders always refused.
4. ✅ `session_recovery.py` prints the staleness block on a fixture with a
   registered worktree.
5. ✅ `python scripts/qa_compress.py --fast` green (new tests mapped by the
   F-022 name convention), full run unaffected.
6. ✅ Zero model/token usage — pure script + tests.

## Developer Targets

1. `scripts/worktree_cleanup.py` — R1, with module docstring documenting the
   incident motivation + the classify/dry-run/apply discipline.
2. `session_recovery.py` — R2 block (function + print, no restructure).
3. `tests/test_worktree_cleanup.py` — R3.
4. Docstrings per the repo's living-code-docs conventions (F-011).

## Test Criteria

R3 is the test plan. QA additionally verifies R1 by hand against a scratch
repo (not the real pipeline repo) and checks the exit-code contract.

## Tooling Gates (mandatory — QA checks ALL)

```powershell
python scripts/qa_compress.py --fast
python -m py_compile scripts/worktree_cleanup.py scripts/session_recovery.py
```

**Environment:** Python 3, Windows + Linux compatibility, stdlib only.

## Codebase Snapshot

| File | Relevant symbols | Notes |
|------|-----------------|-------|
| `scripts/worktree_setup.py` | creation flow | read-only reference for conventions (argparse, subprocess style) |
| `scripts/session_recovery.py` | scan + print sections | extend with the staleness block |
| `scripts/merge_if_passed.py` | dry-run/apply discipline pattern | mirror its flag semantics |
| `tests/` | existing fixture patterns | follow the repo's tmp-repo fixture conventions |
