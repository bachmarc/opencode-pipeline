# Story 07-02 — Document Reasoning Effort

Status: Planned
Feature: docs (F-003)

## Context / Purpose

The local `opencode.jsonc` supports a per-agent **`reasoningEffort`** setting (e.g.
`"developer": { "model": "provider/cheap", "reasoningEffort": "medium" }`). This is the
third axis of role tuning alongside model assignment and permissions: the same cheap
model can reason shallowly (low) or deeply (high) depending on the agent's job.

The pipeline currently documents only two of the three axes: model assignment
(README "Model Assignment", role vs. machine separation) and Phase-0 enforcement
(`permission.task`). The reasoning depth exists only in the maintainer's local config —
a new machine setup does not learn from the docs that agents should be tuned this way,
and the reasoning budget rationale (QA judges harder than the documenter reconciles) is
lost.

This story closes the documentation gap: the reasoning depth axis becomes part of the
documented per-machine configuration, with the reasoning-budget rationale per role.

## Requirements

- README explains `reasoningEffort` as a per-agent local setting in `opencode.jsonc`
  (alongside `model`), including which values it takes (low / medium / high) and that
  it is optional (unset = model default).
- The local `opencode.jsonc` example in README shows `reasoningEffort` on the agent
  entries (provider-neutral — no concrete model names).
- The README "four agents in detail" table carries a **reasoning depth** column with the
  role-specific budget rationale (architect: high/deep by design; developer: medium;
  qa-manager: high despite cheap model, because verdicts must be strict; documenter: low).
- `docs/design.md` (Documenter-generated summary) mentions the reasoning depth axis in
  its local-configuration context so the next Architect session finds it.
- All portable files stay provider-neutral: no concrete model/provider names
  (self-checks `test_framework.py`, `test_readme_structure.py` must stay green).
- No changes to `agent/*.md` files, commands, scripts, or templates — documentation only.

## Developer Targets (exactly, no more / no less)

- **`README.md`** — three edits:
  1. Section "Local configuration (stays per machine)": extend the `opencode.jsonc`
     example's `agent` entries with `"reasoningEffort": "<low|medium|high>"` and add
     2-4 sentences explaining: reasoning depth is set per agent; it controls how hard
     the model thinks before answering; unset = model default; it travels with the
     local file, like the model assignment.
  2. Section "Model Assignment" (Technical Details): add one short paragraph (3-5
     sentences) — "Reasoning depth: `reasoningEffort`" — stating that model choice and
     reasoning depth are two separate tuning axes on the same cheap model, and that
     the pipeline's rationale is: developer medium (repetitive implementation),
     qa-manager high (verdicts require scrutiny), documenter low (mechanical
     reconciliation), architect unset/strong-model reasoning by default.
  3. Table "The four agents in detail": add a **Reasoning depth** column with the
     per-role values as concrete guidance (architect — high; developer — medium;
     qa-manager — high; documenter — low), each with a ≤6-word rationale.

- **`docs/design.md`** — one edit: in "README Structure" section layout (the
  "How model assignment works" bullet), note that model assignment now covers two
  axes: model AND per-agent reasoning depth (`reasoningEffort`), documented in README
  Local configuration / Model Assignment.

## Acceptance criteria (checked by qa-manager)

- README Local-configuration example contains `reasoningEffort` on at least the four
  pipeline agents (architect, developer, qa-manager, documenter) with placeholder
  values, not concrete model names.
- README Model Assignment section contains the term `reasoningEffort` and explains
  model vs. reasoning-depth as separate axes.
- README agents table has a reasoning-depth column covering all four roles.
- `docs/design.md` README-Structure section mentions the reasoning depth axis.
- `pytest tests/` fully green (especially `test_readme_structure.py` — no model names,
  section order intact — and `test_framework.py`).
- No file outside `README.md` and `docs/design.md` modified.

## Test criteria (must exist BEFORE implementation)

New/extended tests in **`tests/test_readme_structure.py`** (README is the test subject,
the file system is the fake — no external systems):

- `test_readme_local_config_reasoning_effort` — Local-configuration section contains
  `reasoningEffort` on all four agent entries and mentions the value set
  (low / medium / high).
- `test_readme_model_assignment_reasoning_axis` — Model Assignment section contains
  `reasoningEffort` and distinguishes the two axes ("model" and reasoning depth) in
  prose (keyword assertions: "axis"/"axes" or "separate").
- `test_readme_agents_table_reasoning_column` — the agents detail table has a
  reasoning-depth column whose header cell matches /reasoning/i and all four role rows
  carry one of low|medium|high.
- `test_design_mentions_reasoning_effort` — `docs/design.md` contains `reasoningEffort`
  in its README-Structure/model-assignment context.

All tests are deterministic string/structure assertions against the repo's own files
(established self-check pattern) and must exist and FAIL before the README/design edits
are applied.