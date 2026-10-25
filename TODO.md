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
