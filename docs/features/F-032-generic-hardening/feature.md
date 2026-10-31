---
id: F-032
title: Generic Pipeline Hardening — invariants, boundaries, regression nets, main health
status: done
owner: ""
req: []
---

## Vision

The pipeline becomes generically robust: the four project-independent bug
classes from the VirtOffice retrospective (lifecycle ordering, boundary
underspecification, fix-without-regression-net, silent main decay) are
closed by template/prompt rules plus deterministic checks — not by project
specialization. No WebRTC/WASM/infra specifics enter the framework; projects
that need them declare a process profile (`test_strategy`) instead.

Token goal: every new guard is deterministic-first (scripts, ~0 LLM tokens)
or planning-time-only (architect checklist lines); QA tokens do not grow.

## Context

**Input:** the VirtOffice bug retrospective (2026-10-31 — owner-provided
dataset, kept owner-local, NOT in the repo per owner request) — the
dominant finding: QA verifies static correctness; runtime/behavioral
bugs surfaced as USER reports. Root causes: ~35% lifecycle ordering, ~25%
planning gaps (UX/state boundaries), ~20% fake-vs-real divergence,
~10% infra, ~10% QA-unreachable.

**Scope decision (owner, 2026-10-31):** NO project specialization. The
pipeline must stay generic ("keine Spezialfälle verewigen"): no trigger-word
lists (WASM/WebRTC/GPU), no infra story category, no audio/video
observability defaults. The generic carrier for such needs already exists:
`.pipeline/process.json` profiles (`test_strategy: unit-fake | e2e-docker |
custom`) — a future WebApp-like project declares its profile; QA criteria
switch accordingly (shipped in 30-04).

**What remains valid generically (this feature):** ordering invariants and
boundary questions are properties of ANY stateful software, not of
webapps; fixes without regression nets recur in every project; and the
main-decay class was observed in THIS repo (8 pre-existing FAILs blocked
every wave-1 merge; 29-01 was a phantom story — doc exists, code never
implemented, nothing noticed for weeks).

## Requirements (feature level)

1. **Ordering invariants as planning output (L1):** stories touching
   multi-step lifecycles (start/stop, publish/subscribe, join/leave,
   transactional sequences) carry an `Ordering & Recovery Invariants`
   section in test criteria — generic rule, architect decides applicability
   per story (no trigger-word automation).
2. **Boundary checklist in planning (L5):** a short generic question set
   the architect answers per feature: degenerate/empty inputs; visible
   intermediate states during transitions; abort/error mid-flight;
   repeat/reconnect/idempotency; environment matrix where it runs. UnClear
   answers MUST become `[NEEDS CLARIFICATION]` markers (plan_check already
   FAILs on those — generation and enforcement finally meet).
3. **Bugfix completeness (resolution pattern §4.1):** a bugfix story is
   PASS only if a regression test exists that would have caught the bug
   (repro of the failure). One rule line in the QA prompt.
4. **Main health, deterministic (this session's data):** `merge_if_passed.py`
   runs the configured test suite on main right after a successful merge;
   FAIL → loud error JSON (no rollback) + fix-story obligation note. This
   would have caught the 8-FAIL rot at the first wave-1 merge instead of
   weeks later.
5. **Stale-planning reminder (phantom 29-01 class):** `driver.py next`
   emits `stale-planned` for stories Planned longer than a threshold with
   no open intent/worktree — surfaces forgotten stories deterministically.
6. **29-01 debt:** implement `worktree_cleanup.py` (classify → dry-run →
   `--apply`, never touches unmerged branches) — the story existed since
   Phase 29, never implemented, and the manual cleanup this session is
   exactly what it exists to prevent.

## Architecture decisions

- **Prompt/template changes are planning-time only:** checklist lines and
  template sections cost architect tokens once per feature, zero QA
  tokens. No new checker for invariants existence — applicability is a
  judgment (lifecycle or not), not a pattern; plan_check enforces the
  MARKERS, not the judgment (anti over-mechanization).
- **Deterministic guards ride existing scripts:** main-health in
  `merge_if_passed.py` (post-merge step), stale-planned in `driver.py`
  (new action kind, stable order last before escalate kinds), cleanup as
  standalone script. No new entry points.
- **Non-goals (deliberate):** no fake-fidelity trigger lists, no infra/
  deploy gates, no observability defaults, no per-domain templates. Those
  are project profiles, not framework rules.

## Stories

- 32-01-boundary-invariants-prompts (planned) — template + architect +
  qa-manager prompt rules (req 1–3)
- 32-02-main-health-driver (planned) — merge_if_passed post-merge suite
  check + driver stale-planned (req 4–5)
- 32-03-worktree-cleanup (planned) — 29-01 debt, `worktree_cleanup.py`
  (req 6)

## Open questions / follow-ups

- None blocking. 32-03 is deletable at the checkpoint if the owner prefers
  housekeeping-only handling of future worktree accumulation.

## References

- VirtOffice bug retrospective (owner-local dataset, removed from the repo
  per owner request; lessons L1/L5/§4.1)
- This session's evidence: 8 pre-existing FAILs on main (30-06),
  phantom story 29-01, manual worktree cleanup of 8 merged trees.
- Shipped substrates this builds on: plan_check marker enforcement
  (30-05), driver action framework (30-01/30-02), merge gate
  (merge_if_passed.py), process profiles (30-04).