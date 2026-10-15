# Story 28-01 — Architect Prompt: Pure-JS Dependency Preference

Status: Planned
Feature: Pure-JS Dependency Preference (F-028)

## Codebase Snapshot

- `agents/architect.md` — "Gather requirements" section (lines 38–42), "Design architecture"
  section (lines 43–54). No current guidance on dependency selection criteria.
- `tests/test_architect_prompt.py` — existing tests for architect prompt content. Currently
  has `test_architect_prompt_has_scaffold_runtime_question` (added in 27-01).

## Context / Purpose

Native Node.js addons (`bcrypt`, `argon2`, `sharp`, `sqlite3`) require `node-gyp` compilation
at install time. This breaks silently on: wrong Node.js version, minimal Docker images
(no `python`/`make`/`gcc`), CI environments, cross-platform dev teams. Pure-JS alternatives
exist for most common cases and have the same API — the Architect should know to prefer them.

This is a one-line design decision that should be in the Architect's head for every
Node.js scaffold story — not discovered after a broken CI build.

## Requirements

1. `agents/architect.md` gets a new guidance block in the "Design architecture" section,
   specifically under Node.js/TypeScript projects. The rule:
   > **Dependency selection (Node.js):** Prefer pure-JS/pure-TS npm packages over
   > native-addon alternatives. Native addons require `node-gyp` (needs `python`, `make`,
   > `gcc`) and break on version mismatches. Common swaps:
   > `bcrypt` → `bcryptjs` · `uuid` (already pure) · check `node-pre-gyp` or `binding.gyp`
   > in a package as a native-addon signal. If a native addon is unavoidable, add an
   > explicit "Build requirements" note to the story's Environment Constraints.

2. The rule applies to scaffold stories and any story that adds new npm dependencies.

3. One new test verifies the guidance is present in the prompt.

## Developer Targets (exactly, no more / no less)

- `agents/architect.md`: In the "Design architecture" section, after the existing
  architecture guidance bullets, add a new bullet:
  ```
  - **Dependency selection (Node.js/TypeScript):** Prefer pure-JS/pure-TS packages over
    native addons (packages with `binding.gyp` or `node-pre-gyp`). Native addons require
    `node-gyp` (needs `python`, `make`, `gcc`) and break on Node.js version mismatches or
    in minimal Docker/CI environments. Common swaps: `bcrypt` → `bcryptjs`. If a native
    addon is unavoidable, add "Build requirements: node-gyp, python, make" to the story's
    `## Environment Constraints` section.
  ```
- Update docstring/module header in `agents/architect.md` if applicable.
- `tests/test_architect_prompt.py`: Add test `test_architect_prompt_has_pure_js_preference` —
  asserts "bcryptjs" and "native addon" (or "native-addon") present in `agents/architect.md`.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `agents/architect.md` contains "bcryptjs" and "native addon" guidance in the design section.
- `tests/test_architect_prompt.py::test_architect_prompt_has_pure_js_preference` exists and passes.
- No existing tests broken.

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (`pytest`)
- [ ] Lint clean — N/A (no lint checker in framework's qa_config.json)
- [ ] Typecheck clean — N/A
- [ ] Format check clean — N/A
- [ ] Audit clean — N/A

## Test criteria (must exist BEFORE implementation)

- `tests/test_architect_prompt.py::test_architect_prompt_has_pure_js_preference` — reads
  `agents/architect.md`, asserts both "bcryptjs" and "native addon" are present.
  Protects: ensures the VirtOffice class of native-addon breakage is explicitly addressed
  in the Architect's decision framework — not just known tribal knowledge.
