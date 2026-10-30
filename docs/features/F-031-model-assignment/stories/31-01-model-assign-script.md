# Story 31-01 — model_assign.py: deterministic tier→model appliance

Status: Planned
Feature: Model Assignment (F-031)

## Codebase Snapshot

- `scripts/` — existing scripts follow a stdlib-only CLI pattern with JSON
  output and defined exit codes (see `scripts/intent.py`, module docstring
  pattern). New script conforms.
- `AGENTS.md` — role abstraction rule: no model/provider names in portable
  files; model assignment lives in local gitignored config only.
- `.gitignore` — must gain the `model_map.json` entry (repo-local guard) IF
  the map file can appear in the repo root; primary location is
  `~/.pipeline/model_map.json` (outside repo).
- Existing self-check tests: `tests/test_framework.py` style — read repo
  files, run scripts via subprocess, assert invariants.

## Context / Purpose

The user frequently reassigns agent roles to different models/providers
(ollama, openrouter, opencode…) under token scarcity. Currently this happens
via conversation with the architect, which produces an endless discussion
about how/what/where to change it — expensive tokens for what is a
deterministic file edit. This story ships the applier script: read the local
`model_map.json`, write the local `opencode.jsonc`. The architect never
discusses assignments again; the script's one-line confirmation is the whole
interaction.

## Requirements

1. Create `scripts/model_assign.py` with subcommands:
   - `--show`: print the current mapping as JSON
     (`{role: {tier, provider_model}}`) from the map file. Missing map →
     exit 1 with hint to run `--init`.
   - `--init`: write a minimal default map to the map path (roles: architect,
     developer, qa-manager; empty `provider_model`, `tier: "cheap"` for all
     — user fills in). Exit 1 if the map already exists (no silent
     overwrite).
   - `--apply`: patch local `opencode.jsonc`: for every role present in BOTH
     the map and the config's `agents` object, set `model` to the map's
     `provider_model`. Print JSON result:
     `{result: "PASS", applied: {"architect": "opencode/x", ...}}`.
2. Paths overridable: `--map <path>` (default `~/.pipeline/model_map.json`),
   `--config <path>` (default `~/.config/opencode/opencode.jsonc`).
3. JSONC safety: `opencode.jsonc` may contain comments. Patch ONLY
   `agent.<role>.model` value patterns (`"model": "..."` lines inside the
   role object). If the file cannot be patched unambiguously (role missing,
   two `model` keys in one role block, trailing syntax uncertainty), exit 1
   WITHOUT writing.
4. Never validate/pad/interpret model strings — they are opaque.
5. The script contains NO model or provider names in its code or help text
   (role abstraction).
6. Windows/Linux path safe via pathlib only (repo portability rule).

## Developer Targets (exactly, no more / no less)

- Create `scripts/model_assign.py` (module docstring: purpose, subcommands,
  conventions).
- Create `tests/test_model_assign.py` with a fake `--map`/`--config` fixture
  directory (monkeypatched home or explicit path flags — flags make tests
  hermetic).
- Add `model_map.json` to `.gitignore` (repo-root defense in depth).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `--show` on a valid fixture map prints exactly the mapping JSON, exit 0.
- `--apply` on a fixture opencode.jsonc changes ONLY the three `agent.*.model`
  lines; all other config content byte-identical; comments preserved.
- `--apply` with a map role NOT present in config's agents → that role is
  skipped, reported in result as `skipped`.
- `--apply` with ambiguous config (duplicated model key) → exit 1, file
  unchanged.
- `grep -rE "(ollama|openrouter)" scripts/model_assign.py` finds NOTHING
  (role abstraction self-check).

## Test criteria (must exist BEFORE implementation)

- `tests/test_model_assign.py::test_apply_patches_model_lines` — before/after
  text comparison: only model lines changed, comment lines preserved.
- `tests/test_model_assign.py::test_apply_refuses_ambiguous` — duplicated
  model key in role block → exit 1, file bytes unchanged.
- `tests/test_model_assign.py::test_apply_skips_missing_roles`.
- `tests/test_model_assign.py::test_show_missing_map_exits_1`.
- `tests/test_model_assign.py::test_init_creates_minimal_map` — second
  `--init` run exits 1 (no overwrite).
- `tests/test_model_assign.py::test_no_model_names_in_script` — reads the
  script source, asserts no provider/model name pattern beyond the generic
  role names.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black)
