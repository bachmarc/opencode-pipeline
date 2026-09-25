---
id: F-021
title: Documenter Scope Fix
status: in-progress
owner: ""
req: []
---

## Vision

The documenter check in `merge_if_passed.py` and `documenter-guard.ts` correctly detects
whether the Documenter has run on the current feature branch — not on any ancestor commit.
`README.md` and `AGENTS.md` are up-to-date with all merged stories.

## Context

`git log <branch> --grep="docs: reconcile"` traverses the full ancestry, including `main`.
Because Phase 12 left several `docs: reconcile` commits on `main`, every feature branch
inherits them — so the check always passes, even when the Documenter never ran on that branch.

The fix is to scope the log to branch-exclusive commits only:
`git log main..<branch>` (or equivalently `git log <branch> ^main`).

The same bug exists in two places:
1. `scripts/merge_if_passed.py` — `check_documenter_commit()`
2. `plugins/guards/documenter-guard.ts` — `git log ${branch}` call

After the fix, all merges since Phase 13 that bypassed the check need a catch-up
Documenter run to bring `README.md` and `AGENTS.md` up to date.

## Stories

- 21-01-documenter-scope-fix (in-progress)
- 21-02-documenter-catchup (planned)
