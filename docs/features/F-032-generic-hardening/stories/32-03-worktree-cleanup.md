# Story 32-03 — worktree_cleanup.py (29-01 debt)

Status: Done
Feature: Generic Pipeline Hardening (F-032)

## Codebase Snapshot

- `scripts/worktree_setup.py` — worktree creator: `worktree_exists`,
  `is_main_clean` (~line 65), `cmd_create` (~line 83:
  `.worktrees/<id>-<slug>`, branch `feature/<id>-<slug>`), remove/list
  subcommands exist. Nothing in the repo ever removes merged worktrees
  (this story's gap).
- `scripts/session_recovery.py` — session start scan (intents, QA state,
  worktrees list). Candidate integration point: staleness hint line.
- `.pipeline/intent.json` — intents carry `worktree`/`branch` fields
  (created by `intent.py start --worktree/--branch`).
- `docs/features/F-029-worktree-hygiene/stories/29-01-worktree-cleanup-script.md`
  — the original (never implemented) story doc: classify → dry-run default
  → `--apply` removal with labeled stash protection; `--purge-folders` for
  unregistered leftovers; never touches unmerged branches. This story
  implements that contract, superseding specific clauses where safer or
  simpler (audit 2026-10-31): SUPERSEDES R1.3 exit codes (dry-run exits 0),
  SUPERSEDES R1.4 stash protection + prune step (this story only removes
  clean merged trees — nothing needs stashing; dirty/unmerged survive
  untouched); KEEPS R1.5 purge contract (purge requires --apply, orphans
  without `.git` link only).

## Context / Purpose

This session ended with 8 merged, clean worktrees that had to be removed
MANUALLY (git worktree remove --force × 8 + branch -d × 8) — exactly the
mechanical work 29-01 was written to prevent, and 29-01 itself was a
phantom story (never implemented). Worktree accumulation is a generic
pipeline property: every story creates one, nothing removed them. The
script makes removal deterministic, safe (never touches unmerged branches),
and zero-token (dry-run default, `--apply` opt-in — the repo's merge
discipline pattern).

## Requirements

1. `scripts/worktree_cleanup.py` (stdlib-only):
   - `list` (default): for every git-registered worktree: classify
     `merged` (branch merged into main/master) / `unmerged` / `dirty`
     (uncommitted changes) and print a JSON plan. `.worktrees/` folders NOT
     registered with git are listed as `orphan-folder` (count only).
   - `--apply`: remove ONLY worktrees classified `merged` AND clean —
     `git worktree remove` + `git branch -d` (the safe delete: refuses
     unmerged). NEVER unmerged or dirty ones. Output JSON: removed entries
     with branch names.
   - `--purge-folders`: REQUIRES `--apply` (29-01 R1.5 contract): delete
     orphan `.worktrees/` folders WITHOUT a `.git` link file (inert
     remnants); folders WITH a dead `.git` link are reported for manual
     review, never deleted.
   - Exit codes (SUPERSEDES 29-01 R1.3 — dry-run exits 0 always): `list` and
     `--apply` exit 0 with the plan/summary; exit 1 only on git errors.
     `list` is the default and always safe (no mutation).
2. `scripts/session_recovery.py`: add ONE staleness summary line (count of
   merged-but-present worktrees + cleanup hint) to the existing worktree
   block — surfaces the accumulation at every session start, zero tokens.
3. NO changes to `worktree_setup.py`, `merge_if_passed.py`, or any prompt.

## Developer Targets (exactly, no more / no less)

- `scripts/worktree_cleanup.py` (new) per req 1, module docstring documents
  classification, flags, exit codes.
- `scripts/session_recovery.py` — the one staleness line in the worktree
  block.
- `tests/test_worktree_cleanup.py` (new) per test criteria.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- Fixture repo: merged+clean worktree → `list` classifies `merged`;
  `--apply` removes worktree AND deletes branch; unmerged and dirty
  worktrees survive `--apply` untouched (the core safety property).
- `--purge-folders` deletes only orphan folders without `.git` link; a
  folder WITH a dead `.git` link is reported, not deleted.
- Default call (`list`) mutates nothing.
- `session_recovery.py` prints the staleness line when merged worktrees
  exist.

## Test criteria (must exist BEFORE implementation)

- `tests/test_worktree_cleanup.py::test_list_classifies_merged_unmerged_dirty`
- `tests/test_worktree_cleanup.py::test_apply_removes_merged_clean_only` —
  unmerged + dirty untouched.
- `tests/test_worktree_cleanup.py::test_apply_refuses_unmerged_branch_delete`
- `tests/test_worktree_cleanup.py::test_purge_folders_orphans_only`
- `tests/test_worktree_cleanup.py::test_purge_folders_reports_dead_git_link`
- `tests/test_worktree_cleanup.py::test_default_list_mutates_nothing`
- `tests/test_worktree_cleanup.py::test_session_recovery_staleness_line`

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest per `qa_config.json`)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black)