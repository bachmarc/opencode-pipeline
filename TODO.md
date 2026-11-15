# TODO — opencode-pipeline backlog

Unprocessed improvement ideas. Not stories yet — promote into
`docs/features/F-0XX-*/` + `STORIES.md` when scheduled.

---

## T-001 — Developer-agent loop protection: step budget, item-wise spawns, anti-loop prompts

**Source:** VirtOffice session 2026-10-25 (story 26-09, E2E exploration,
GLM-5.3-Flash developer agent). A long-running exploration subagent got stuck
in an infinite loop with chaotic output; together with server restarts the
run needed 4 attempts. User-observed.

**Ideas:**

1. **Step budget for developer agents:** recommend/document
   `agents.developer.steps` (e.g. 60-80) in the project-local `opencode.jsonc`
   — OpenCode removes tools at the cap and forces a summary, so a looping
   agent is bounded instead of running forever.
2. **Item-wise spawns:** architect guidance — cut long exploration /
   verification work into item-level subagent spawns (one matrix item or a
   small group per spawn) with incremental-commit discipline, so aborts and
   restarts lose at most one item of work.
3. **Anti-loop rules in developer prompts:** hard rule — "never repeat the
   same failing action more than 2-3 times; mark the item DEFERRED with a
   diagnosis and move on".

**Status:** idea (unscheduled)

---

## T-002 — Status-booking pipeline defects: merge must maintain the driver's status source + booking-vs-git consistency check

**Source:** VirtOffice session 2026-11-15 (pipeline cleanup). Full self-contained
defect report with evidence and fix suggestions:
`docs/reports/2026-11-15-virtoffice-status-booking-defects.md` — READ THAT
REPORT FIRST; it is the problem statement for a future feature (F-0XX +
STORIES.md).

**Findings (D-1 … D-10), short form:**

1. **D-1 (central):** `driver.py` parses story status from the story files'
   `Status:` lines — but `merge_if_passed.py` never updates them → ~35 false
   driver actions (merge-candidates/spawn-qa for merged stories) in VirtOffice.
   Fix: merge writes `Status: Done (merged as <sha>)` atomically.
2. **D-6 (bug-catcher):** no check "claimed done vs actually on main" — two
   VirtOffice stories (43-01/43-02) were booked "✅ DONE" while their commits
   were never merged (work missing on main, found only by manual git
   forensics). Fix: booking-vs-git ancestry check
   (`git merge-base --is-ancestor`).
3. **D-4/D-2:** no first-class terminal states (reverted/dropped/dormant/
   parked/superseded) + case-sensitive `_is_done` → semantic driver noise.
4. **D-5/D-7/D-8/D-9/D-10:** duplicate story-ID detection missing (49-01
   double row, two 48-26 files, two 52-01 stories), QA verdict state recording
   not enforced by the merge flow, stale worktree accumulation, plan_check
   legacy noise without baseline, intents decoupled from story completion.

**Status:** idea (unscheduled) — promote to feature when scheduling.
