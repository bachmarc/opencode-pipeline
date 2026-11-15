# Defect Report — Story-Status Booking Divergence in the Driver Pipeline

**Date:** 2026-11-15
**Source:** VirtOffice cleanup session (architect). User observed: "the driver
output is mostly wrong — much is just wrongly booked." Analysis confirmed it.
**Purpose:** Self-contained problem statement so a future opencode-pipeline
session can turn these into stories (F-0XX feature + STORIES.md). Also tracked
as `TODO.md` → T-002.
**Related scripts:** `scripts/driver.py`, `scripts/merge_if_passed.py`,
`scripts/session_recovery.py`, `scripts/plan_check.py`,
`scripts/create_story.py`, `scripts/story_status.py`.

---

## 1. Summary

`driver.py` (by design, L73–75: *"Story statuses are parsed from the
`Status:` lines of `docs/features/*/stories/*.md` … NOT from the STORIES.md
markdown table"*) reads the story files as the status source of truth — **but
no pipeline step ever maintains that source after a merge.** The merge flow
updates STORIES.md prose and creates the merge commit; the story files keep
their pre-dev status ("OPEN", "✅ QA-PASS (…Merge ausstehend)", "BLOCKED")
forever. On a mature project this produces:

- ~15 false `merge-candidate` actions (verdict PASS in the verdict state +
  story-file status not `Done*` → already-merged stories flagged for merge),
- ~20 false `spawn-qa` actions (story-file status not `Done*` + no verdict in
  the state file → merged stories flagged for QA),
- while the two REAL defects (work never merged, falsely booked as done)
  were hidden inside that noise and only surfaced via manual git forensics.

In the VirtOffice repo (167 stories) the driver emitted ~36 actions of which
**exactly 2 were genuine** (51-01 pending merge; 43-01/43-02 dev-done but
never merged). All others were false positives from booking divergence. A
manual true-up of 49 story files was needed to restore driver usefulness.

---

## 2. Defects

### D-1 — Merge flow never updates story-file `Status:` lines (central defect)

- **Symptom:** driver `merge-candidate`/`spawn-qa` spam for merged stories.
- **Root cause:** `merge_if_passed.py` merges + (at best) the session updates
  STORIES.md, but the story file — the driver's status source — is never
  touched. Nothing in the whole flow (developer, QA, merge, documenter) owns
  the story-file status transition.
- **Evidence (VirtOffice, pre-true-up):** 43-05/06/07/08, 48-01/03/08/09/10/
  11/14/16/17/19, 52-01 all merged (merge commits on main), story files still
  `OPEN`/`QA-PASS (Merge ausstehend)` → 15 false `merge-candidate` actions.
- **Suggested fix:** `merge_if_passed.py` sets the merged story's
  `Status:` line to `Done (merged as <short-sha>)` atomically as part of the
  merge step (it already knows the story ID and the merge commit). This
  single change eliminates the largest noise class AND closes the D-7
  verdict-recording gap for the merged path.

### D-2 — `_is_done` is case-sensitive

- **Root cause:** `driver.py` `_is_done()`: `status.startswith("Done")`.
  VirtOffice story 48-03 carried `Status: DONE (QA-PASS merged)` → not
  recognized → false `merge-candidate`.
- **Suggested fix:** `status.strip().lower().startswith("done")`.

### D-3 — Missing `Status:` line + stored verdict → false `merge-candidate`

- **Symptom:** story 52-01 (comm-mic) had **no** `Status:` line at all;
  status `""` is not `Done*` while a PASS verdict existed → flagged for merge
  although merged.
- **Root cause:** (a) missing status is treated as "not done" instead of
  "unknown"; (b) nothing enforces the presence of a `Status:` line
  (`create_story.py` template discipline exists, but hand-written/legacy
  story files slip through).
- **Suggested fix:** treat missing status as an explicit
  `status-divergence`/`unknown-status` finding (visible, not silent); enforce
  `Status:` line presence in `plan_check.py` for all non-legacy stories.

### D-4 — No first-class terminal states for reverted / dropped / dormant / parked / superseded

- **Symptom:** legitimate closed-but-not-merged outcomes had to be encoded as
  `Done (…)` (semantically wrong) or `Planned (…)` (also wrong) just to
  silence the driver — or they generate permanent noise.
- **Root cause:** the driver vocabulary is only: `""` (ignored), `Planned`
  (ignored), `Done*` (done), **everything else = QA candidate**. Real projects
  accumulate: REVERTED (43-08), DROPPED (48-29), DORMANT (46-01),
  EINGESTELLT (48-02), investigation-closed (48-05/06), superseded
  (48-12 → via 50-02; 44-01-drain → already fixed since 32-04).
- **D-4a — Asymmetric match semantics (observed during the 2026-11-15
  true-up):** `_is_done` matches by PREFIX (`status.startswith("Done")` —
  so `Done (merged as <sha>)` is recognized), but the Planned exclusion in
  `_is_qa_candidate` compares by EXACT EQUALITY (`status != "Planned"` —
  and not `_is_done(status)`). Annotated forms therefore behave
  inconsistently: `Done (reverted a587629)` is driver-silent, but
  `Planned (waiting for go)` does NOT match and keeps producing `spawn-qa`
  noise. Four VirtOffice files (44-01, 46-01, 48-07, 56-01) had to be
  re-encoded as bare `Status: Planned` with the context moved to a separate
  `Note: …` line (commit `106f63b`) — a workaround the status template does
  not prescribe, so the next agent will naively write annotated statuses
  again.
- **Suggested fix:** introduce and document a status vocabulary with
  driver-known classes, e.g. `Done*`, `Planned*`, `Parked*` (dormant /
  eingestellt — driver-neutral), `Closed*` (reverted / dropped / superseded /
  already-fixed — driver-neutral, distinct from Done), `In Progress*`
  (QA candidate). Use CONSISTENT class semantics for every class
  (single `status_class()` parser — prefix match or explicit enum — applied
  by both `_is_done` and `_is_qa_candidate`; no mixed startswith/exact-
  equality logic). Enforce the vocabulary in `plan_check.py`.

### D-5 — No duplicate story-ID detection (STORIES.md rows AND story files)

- **Symptom:** VirtOffice 49-01 appeared **twice** in STORIES.md (one
  `🔲 OPEN`, one `✅ QA-PASS (a3fa01c)`); the stale OPEN row kept the driver
  flagging `spawn-qa` and the intent open for 245h. Additionally two story
  FILES share the 48-26 ID (`48-26-drain-pending-counter.md`,
  `48-26-drain-timeout-fallback.md`) and two different stories were both
  numbered 52-01 — the driver emitted duplicate 48-26 actions.
- **Root cause:** nothing validates ID uniqueness — neither across STORIES.md
  rows nor across story files.
- **Suggested fix:** `plan_check.py` finding `duplicate-story-id` for both
  surfaces (STORIES.md rows, story-file basenames).

### D-6 — No cross-check "claimed done vs actually on main" (the bug-catcher gap)

- **Symptom:** 43-01/43-02 were booked in STORIES.md as `✅ DONE (commit
  8c40b28 / 341917e)` — but neither commit is an ancestor of main. The fixes
  (e.g. the `ResizeObserver` resize-sync) exist ONLY on their branches. The
  work was never merged; the booking lied. This was **the only real defect
  hidden in the driver noise** and it took manual `git merge-base
  --is-ancestor` forensics to find it.
- **Root cause:** the repo has a second landing pattern (direct commits to
  main, e.g. 49-01 `a3fa01c`, 48-28 `04111b1`) that bypasses
  merge_if_passed/QA-verdict/story-status updates entirely; and no script
  ever compares status claims against git ancestry.
- **Suggested fix:** new consistency check (new `booking_check.py` or a
  `session_recovery.py` section): for every story whose status (story file or
  STORIES.md) claims `Done`/`QA-PASS (merged as <sha>)`, verify
  `git merge-base --is-ancestor <sha> main`. Violations surface as
  `booking-vs-git divergence`. This check would have caught 43-01/43-02
  immediately and is the single highest-value guard.

### D-7 — QA verdict state file incomplete; recording not enforced by the flow

- **Symptom:** verdict state contains only the 2026-11-02 QA batch; all later
  QA-PASS merges (48-20…28, 49-01, 51-01, 52-01) exist only as prose in
  STORIES.md/commit messages. Driver then flags merged stories as
  `spawn-qa` ("status OPEN with no QA verdict").
- **Root cause:** verdict recording is a side effect of specific QA-manager
  sessions, not an enforced artifact of the merge/QA flow.
- **Suggested fix:** `merge_if_passed.py` requires and writes the verdict
  entry as part of the merge (making the verdict state the authoritative
  merge ledger); sessions that merge without a recorded verdict get a
  hard error instead of silent drift.

### D-8 — Stale worktrees accumulate; cleanup not part of the merge flow

- **Symptom:** 8 merged-but-present worktrees in VirtOffice;
  `session_recovery.py` prints a staleness hint but nothing acts on it and
  the reminder gets ignored across sessions.
- **Suggested fix:** `merge_if_passed.py` prints (or runs, with consent) the
  exact `worktree_cleanup.py` invocation for the merged branch; consider
  making session-recovery staleness an actionable driver item.

### D-9 — `plan_check.py` legacy noise: no baseline

- **Symptom:** on a mature project, plan_check emits hundreds of
  `missing-section` findings for legacy stories written before the current
  template discipline (VirtOffice: ~200 findings across phases 01–49) — real
  new findings drown.
- **Suggested fix:** baseline/scoping option (e.g. `--since <story-id>`,
  ignore-list file, or per-phase opt-out) plus severity classes
  (new-story-blocking vs legacy-informational).

### D-10 — Intent tracking decoupled from story completion

- **Symptom:** the 49-01 intent stayed open for 245h although the work landed
  on main (`a3fa01c`); only a manual `intent.py` close resolves it.
- **Suggested fix:** driver/session-recovery cross-references open intents
  against story `Done*` status and emits a concrete closure suggestion
  ("work appears done via story XX — `intent.py done`?") instead of a bare
  age reminder.

---

## 3. Suggested remediation order

1. **D-1** merge updates story-file status (+ D-7 verdict recording) — kills
   the largest noise class permanently and makes the status source real.
2. **D-6** booking-vs-git consistency check — the actual bug-catcher; the only
   guard that would have caught the two real VirtOffice defects.
3. **D-4 + D-2** terminal-state vocabulary + case-insensitivity — driver
   semantic correctness.
4. **D-5, D-8, D-9, D-10** — hygiene items.

## 4. Reproduction / evidence pointers

- Repo: `C:\Users\D052074\Development\virtoffice`, driver noise observed at
  2026-11-15 with `python ~/.config/opencode/scripts/driver.py next` before
  the manual true-up (pre-true-up state reproducible at commit `b844454`).
- Manual true-up applied 2026-11-15: 49 story files re-booked to truthful
  statuses (this report documents the pre-true-up state).
- Driver source quotes: `_is_done` (`status.startswith("Done")`),
  `_is_qa_candidate` (`status != "" and status != "Planned" and not
  _is_done(status)`), status source note L73–75.
- VirtOffice concrete before-states (story file status → reality):
  - `43-05/06/07/08`, `48-01/08/09/10/11/14/16/17/19`, `52-01×2`: OPEN /
    QA-PASS-ausstehend → all merged on main.
  - `48-20…48-28`: OPEN → all merged on main (status commits e.g. `ac6fe46`,
    `d6b915e`, `f94ce7f`, `e2bdfaa`, `71598c3`, `fa8b68e`).
  - `49-01`: OPEN → work directly on main as `a3fa01c`; duplicate STORIES.md
    row removed during true-up.
  - `43-01/43-02`: "✅ DONE (commit 8c40b28/341917e)" in STORIES.md → commits
    NOT ancestors of main; fixes live only on branches
    `feature/43-01-browser-resize-sync` / `feature/43-02-screenshare-modal-pan-blocking`.
  - `48-03`: `Status: DONE (QA-PASS merged)` (uppercase) → not recognized as
    done by `_is_done`.
