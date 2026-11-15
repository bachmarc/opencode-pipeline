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
   Plus **D-4a (asymmetry):** `Done` is matched by prefix (`startswith`) but
   `Planned` by exact equality (`status != "Planned"`) — annotated
   `Planned (...)` statuses keep triggering spawn-qa; VirtOffice had to
   re-encode to bare `Planned` + `Note:` line (commit 106f63b).
4. **D-5/D-7/D-8/D-9/D-10:** duplicate story-ID detection missing (49-01
   double row, two 48-26 files, two 52-01 stories), QA verdict state recording
   not enforced by the merge flow, stale worktree accumulation, plan_check
   legacy noise without baseline, intents decoupled from story completion.

**Status:** idea (unscheduled) - promote to feature when scheduling.

---

## T-004 — host.docker.internal:host-gateway unreliable on Linux Docker (44-01-v2 production finding)

**Source:** VirtOffice event deployment 2026-11-15. LiveKit Prometheus showed "unreachable" in
production despite correct `extra_hosts: host-gateway` in docker-compose.prod.yml.

**What happened:** The backend container used `extra_hosts: ["host.docker.internal:host-gateway"]`
to reach LiveKit Prometheus (port 6789, `network_mode: host`). This looked correct in review
but `host.docker.internal` did not resolve in production on the Linux Docker host — every poll
returned null, showing "LiveKit unreachable" and 0/300 UDP slots in the admin dashboard.

**Workaround (immediate):** Set `LIVEKIT_PROMETHEUS_URL=http://<gateway-ip>:6789/metrics` in
`.env`, where `<gateway-ip>` is the Docker bridge gateway IP discovered via:
`ip route | grep docker0` or `docker network inspect <network> | grep Gateway`.
The env var is already implemented in `metrics-scraper.ts` and overrides the default URL.

**Suggested fix for the story/docs:**
- README-DEPLOY.md §12: document the `host.docker.internal` Linux caveat and the
  `LIVEKIT_PROMETHEUS_URL` fallback with the `ip route` discovery command.
- Consider using the bridge gateway IP as the primary default on Linux.
- Story 44-03-v2 (docs-only): update README-DEPLOY + .env.example with explicit guidance.

**Status:** idea (unscheduled) — workaround available via env var.

**Source:** VirtOffice session 2026-11-15 (story 51-01 reconcile, ses_e1ff80cecffe6TIB4tgfrLRHdA).

**What happened:** The `documenter` subagent failed with the Ollama error
`"you have reached your session usage limit"` (ref: 8267aa2b-9e4e-4e12-958f-8d3eb2fc82c3).
The merge of story 51-01 was blocked because `merge_if_passed.py` requires a
`docs: reconcile` commit on the branch, and the documenter could not run. The
architect had to fall back to doing the reconcile manually in the worktree.

**Issues:**
1. **No fallback / retry path:** when a subagent hits a usage limit, the
   pipeline has no documented fallback. The architect is left to either wait,
   add credits, or do the reconcile manually — none of which is documented.
2. **Manual reconcile by the architect is undocumented:** the architect CAN
   do docs-only reconcile work (story files, docstrings in the worktree),
   but this is nowhere documented as a valid fallback when the documenter
   is unavailable. The constraint "Architect writes NO code" applies; the
   reconcile scope (docs, story files, module headers) is within bounds.
3. **worktree_setup.py SyntaxWarning:** `'\s'` invalid escape sequence
   (line 2) — cosmetic but noisy. Should be `r'\s'` or `'\\s'`.

**Suggested fix:**
- Document the "architect manual reconcile" fallback in the merge process
  (AGENTS.md or the merge flow doc): when documenter is unavailable, the
  architect may commit `docs: reconcile` directly in the worktree, scoped
  to story files and module docstrings only (no logic changes).
- Fix the `worktree_setup.py` SyntaxWarning.
- Consider documenter-skip flag in `merge_if_passed.py` for investigation/
  analysis stories that have no production code changes (docs-only branches).

**Status:** idea (unscheduled) - promote to feature when scheduling.
