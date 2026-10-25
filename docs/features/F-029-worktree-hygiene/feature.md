---
id: F-029
title: Worktree Hygiene
status: planned
owner: ""
req: []
---

## Vision

Worktrees are a core pipeline mechanic (one per story, created by
`worktree_setup.py`) — but nothing ever removes them. The pipeline grows a
deterministic hygiene capability: a zero-token cleanup script plus a
session-start staleness check, so stale worktrees can never accumulate
silently across stories again.

## Context

**VirtOffice incident (2026-10-25, architect post-mortem):**

- After ~30 merged stories, the project carried **7 git-registered stale
  worktrees** (stories 22-07, 23-01, 25-02 … 25-06) plus ~50 unregistered
  leftover folders under `.worktrees/`.
- **Cost:** the opencode server spawns a **Playwright-MCP server plus git/file
  watchers for every git-registered worktree at every server start**
  (verified in `opencode.log`: `mcp connected server=playwright` per worktree
  directory). Seven registrations = eight MCP instances + watcher fleets per
  restart — heavy process load on every session start for zero benefit.
- **opencode `worktree_remove` limitations observed:**
  1. Records pointing at deleted directories fail with "the directory does
     not exist" and CANNOT be cleaned via the tool (25 such stale records
     accumulated in the opencode project record store).
  2. Folders whose git registration was pruned (but which still exist on
     disk) fail with "Unable to remove worktree" — the tool delegates to
     `git worktree remove`, which no longer knows them.
  3. Dirty worktrees are (correctly) refused — but there is no guided
     stash-then-remove path.
- Manual cleanup required: per-worktree dirtiness checks, two labeled
  `git stash push` backups, `git worktree remove`, `git worktree prune`, and
  left ~50 inert folders behind (deletion intentionally deferred to the user
  because unregistered dirs cannot be dirtiness-checked via git).

**Root cause (systematic):** `worktree_setup.py` creates; no component
removes. Neither the architect program (session start) nor the story merge
flow (`merge_if_passed.py`) performs worktree teardown or staleness checks.

## Requirements (feature level)

1. **Deterministic cleanup** — `scripts/worktree_cleanup.py`, zero token
   usage, stdlib-only, dry-run by default, safe by construction:
   never touches unmerged branches, stash-protects dirty trees.
2. **Regular architect check** — `session_recovery.py` prints a worktree
   staleness summary (counts + cleanup hint) so every session start surfaces
   the state without any agent decision-making.
3. **Self-check** — pytest coverage against a fixture repo, wired into the
   existing `qa_compress.py` runner.

## Architecture decisions

- **Classify before act:** each worktree is classified (merged into default
  branch? dirty? registered?) and the plan is printed before anything runs.
- **Dry-run is the default** — `--apply` is the explicit opt-in (mirrors the
  repo's `merge_if_passed.py` discipline).
- **Unregistered leftover folders** (git pruned, folder remains) cannot be
  dirtiness-checked via git → the script REPORTS them; deletion only via a
  dedicated `--purge-folders` flag, and only for folders WITHOUT a `.git`
  link file. Folders with a dead `.git` link are flagged for manual review.
- **The opencode record store is out of scope** for the script (tool
  limitation — see Context). The script reports the count of stale opencode
  records where cheaply detectable; actual record cleanup happens via
  `opencode worktree remove` while the directory still exists, or upstream
  tooling.

## Open questions / follow-ups

- **Upstream report (needs user go):** `opencode worktree remove` should be
  able to clean its own records when the directory no longer exists, and
  handle pruned-but-present folders. Candidate for the `report` skill.
- Candidate integration: `merge_if_passed.py` could offer teardown of the
  merged story's worktree after merge (separate story if wanted).

## References

- Incident details: VirtOffice session 2026-10-25 (architect conversation),
  `git worktree list` before/after, `opencode.log` startup sequence.
- Related scripts: `worktree_setup.py` (creator), `session_recovery.py`
  (session-start scan), `merge_if_passed.py` (merge discipline pattern).
