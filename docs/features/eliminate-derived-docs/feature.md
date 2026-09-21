---
id: F-010
title: Eliminate Derived Docs
status: done
owner: ""
req: []
---

## Vision

When this feature is done, `docs/requirements.md` and `docs/design.md` no longer exist
anywhere in the framework — not as files, not as scaffold targets, not as Documenter
duties, not as test assertions. The pipeline maintains a single source of truth
(features + stories + AGENTS.md) with zero duplication. The Architect gets a quick-start
from `session_recovery.py` (already mandatory) + `FEATURES.md` (one read) — both always
current because they read live data or are the index itself.

## Context

F-005 (Doc Model Reform) shifted the documentation model from "architect-docs are primary"
to "features/stories are primary, requirements.md and design.md are derived summaries
maintained by the Documenter." In practice, this created a worse problem: two sources of
truth where the derived copy drifts immediately. Evidence: requirements.md showed 7
features (actual: 10), F-004/F-006 as "Planned" (actual: Done), F-007/F-009 missing
entirely. design.md had similar staleness.

The Documenter is supposed to keep them current, but:
- It runs per-story (after QA-PASS), not globally — so cross-feature summaries lag
- The cheap model often skips the summary update (it's a low-priority reconciliation task)
- Even when updated, the next feature addition makes it stale again

The fix is not "make the Documenter better at updating" — it's "stop duplicating data."

**What replaces them:**
- `FEATURES.md` — human-readable feature index (already exists, always current)
- `docs/features/*/feature.md` — vision, context, architecture decisions per feature
- `AGENTS.md` — NFRs, core rules, out-of-scope (already exists)
- `session_recovery.py` — live pipeline state at session start (already mandatory)

**What does NOT belong in this feature:**
- Changing the feature/story model itself
- Changing session_recovery.py or pipeline_status.py behavior
- Removing FEATURES.md or STORIES.md

## Stories

- 14-01-remove-derived-docs (planned) — Remove requirements.md + design.md from the entire framework
