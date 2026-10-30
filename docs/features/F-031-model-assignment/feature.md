---
id: F-031
title: Model Assignment — deterministic tier→model mapping, no LLM discussion
status: planned
owner: ""
req: []
---

## Vision

Changing which model or provider (`ollama`, `openrouter`, `opencode`, …)
backs an agent role is a 10-second deterministic write — never a
conversation. A local `model_map.json` is the single source of truth
(role → provider/model), a helper script applies it to the local
`opencode.jsonc`, and the architect is freed BY RULE from structuring,
explaining, or discussing model/provider assignments in dialogue. Under token
scarcity the user reassigns roles across providers frequently; after this
feature, each reassignment is one command plus one result line.

The pipeline also encodes the cost-biased default discovered by the user's
testing: the architect runs on the CHEAP tier by default, with defined
escalation points (planning checkpoint, BLOCKED_Design, debug-story-driven
replanning) — the strong tier is the exception, applied via the same
deterministic assignment path.

## Context

**User findings (2026-10-30):**

1. Token scarcity forces frequent model/provider reassignments; the "how" is
   a recurring annoyance: the user tells the architect "switch architect to
   model X and here is what the other agents should use" — and then an
   endless model discussion starts about how/what/where to change it.
2. The architect's own test showed a cheap-tier model suffices ~99% for the
   architect role; the expensive tier was mostly burned on mechanical
   orchestration (see F-030 driver) and verbose self-modification.
3. Role abstraction rule (repo): model/provider names must NOT appear in
   portable files (`agents/`, `command/`, `skills/`, `templates/`,
   `scripts/`). Model assignment must therefore live in LOCAL, gitignored
   files only.

## Requirements (feature level)

1. **Single source of truth:** `~/.pipeline/model_map.json`
   (machine-local, gitignored):
   `{"architect": {"tier": "cheap", "model": "", "provider_model": "opencode/x"},
     "developer": {...}, "qa-manager": {...}}`.
   Tier semantics (`cheap`/`strong`) are user-local conventions; the concrete
   `provider_model` string is opaque to the pipeline.
2. **Applier script:** `scripts/model_assign.py` — `--show`, `--init`, and
   `--apply`: writes the `agent.<role>.model` fields of the LOCAL
   `opencode.jsonc` from the map (textual, deterministic; keeps all other
   config intact). Never contains model names.
3. **No-discussion rule** in `agents/architect.md`: model/provider assignment
   is NEVER discussed, explained, or recommended in dialogue. Full allowed
   reaction to an assignment statement: run the assignment script (or accept
   the user did), confirm the resulting mapping in one line, done.
4. **Architect tier policy flip:** the "expensive/strong model only as
   fallback" line becomes: architect defaults to the CHEAP tier; strong tier
   is applied via escalation paths only (planning checkpoint uncertainty,
   `BLOCKED_Design`, driver `escalate-remedy` diagnosis recommendation from
   F-030 30-02).
5. **QA tier triggers** (added 2026-10-30): cheap tier is the QA default;
   strong-tier QA passes REQUIRED on first pass of new-process-mechanics
   stories, `BLOCKED_Design` diagnosis, and `max_escalations`/breaking-change
   final gates; the qa-manager emits `strong_review_recommended` in its
   verdict, the architect applies the switch — no-discussion rule applies.
   Rationale: QA is the highest-frequency agent (cost) AND its false-PASS
   launders merges (failure asymmetry) — cheap default with bounded strong
   exceptions is the only policy satisfying both. The `provenance` markers
   from F-030 30-04 make tier adequacy measurable over time.

## Architecture decisions

- **The script is fully local-side-effect only:** it reads
  `~/.pipeline/model_map.json` and the local `opencode.jsonc` (paths
  overridable via `--map` / `--config` flags for testability); stdlib-only;
  no network, no validation of provider availability.
- **JSONC safety:** `opencode.jsonc` may contain comments; the applier edits
  ONLY the `agent.<role>.model` value lines via targeted regex, and refuses
  to run when the file contains a syntax it cannot safely patch (fail loudly,
  ask for `--init` which writes a fresh minimal map).
- **Portable-file cleanliness:** guard test proves NO model/provider name
  lands in `scripts/model_assign.py` (role-abstraction self-check pattern).

## Stories

- 31-01-model-assign-script (planned)
- 31-02-architect-tier-policy (planned)

## Open questions / follow-ups

- Driver integration: on `escalate-remedy`, the architect (not the driver) in
  v1 decides the concrete reassignment and applies it via `model_assign.py`
  (F-030 deferred full autonomy).
- Multi-project users: the map is per machine; per-project overrides via
  `<project>/.pipeline/model_map.json` are a candidate follow-up.

## References

- User interview 2026-10-30 (modellwechsel annoyance, flash-architect test).
- Role abstraction rule in `AGENTS.md` (no model names in portable files).
- Related feature: F-030 Process Driver (escalation actions feed this).
