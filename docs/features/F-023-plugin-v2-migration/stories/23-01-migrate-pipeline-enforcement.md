# Story 23-01 — Migrate pipeline-enforcement.ts to OpenCode V2 Plugin API

Status: Planned
Feature: plugin-v2-migration (F-023)

## Context / Purpose

`plugins/pipeline-enforcement.ts` was written for OpenCode V1. Since the upgrade to V2 it fails
to load at every startup with `SchemaError(Missing key at ["default"])` — all six guards
(merge, dev-start, architect-code, story-status, session-recovery, documenter) are inactive.

The V1 entrypoint is a named export of an async factory function that returns a plain object of
hook strings. V2 requires `export default Plugin.define({ id, async setup(ctx) })` from the
`@opencode/plugin` package (no `-ai` suffix in the package name). Hook registration moves from
returned object keys to `ctx.tool.hook("execute.before", ...)` calls inside `setup`.

The six guard modules (`guards/*.ts`) and helper (`helpers/session-state.ts`) contain no V1
plugin API calls — they are plain TypeScript modules and do not need changes. Only the
entrypoint and its package dependency change.

## Requirements

- `plugins/pipeline-enforcement.ts` exports a V2 plugin as `export default Plugin.define({...})`
  with a stable `id: "pipeline-enforcement"`.
- The plugin imports from `@opencode/plugin` (not `@opencode-ai/plugin`).
- All six guards remain functionally equivalent:
  - `tool.execute.before` guard logic (merge, documenter, dev-start, architect-code,
    session-recovery) is registered via `ctx.tool.hook("execute.before", ...)`.
  - `tool.execute.after` guard logic (story-status) is registered via
    `ctx.tool.hook("execute.after", ...)`.
- The V1 context arguments (`directory`, `$`) are replaced by `ctx.location.directory` and a
  locally-spawned child process respectively. [NEEDS CLARIFICATION: `rtk.ts` uses `$` (Bun
  shell helper) for `which` and backtick execution — does `pipeline-enforcement.ts` also use
  `$` for process spawning inside the guards, or do guards call Python scripts differently?]
- `plugins/package.json` dependency updated from `@opencode-ai/plugin` to `@opencode/plugin`.
- The plugin loads without error in V2 (no `SchemaError` in server log).
- No guard logic is removed, weakened, or silently swallowed.

## Developer Targets (exactly, no more / no less)

- Edit `plugins/pipeline-enforcement.ts`:
  - Change import from `import type { Plugin } from "@opencode-ai/plugin"` to
    `import { Plugin } from "@opencode/plugin"`
  - Replace named export `export const PipelineEnforcement: Plugin = async ({ ... }) => { ... }`
    with `export default Plugin.define({ id: "pipeline-enforcement", async setup(ctx) { ... } })`
  - Replace `directory` parameter with `ctx.location.directory`
  - Replace V1 returned hook object with two `ctx.tool.hook(...)` registrations:
    - `await ctx.tool.hook("execute.before", async (event) => { ... })` — all before-guards,
      using `event.tool` (replaces `input.tool`) and `event.input` (replaces `output.args`)
    - `await ctx.tool.hook("execute.after", async (event) => { ... })` — story-status guard
  - The guard modules (`mergeGuard`, `devStartGuard`, etc.) are called identically — only the
    hook registration and context access changes in the entrypoint
- Edit `plugins/package.json`:
  - Change `"@opencode-ai/plugin": "*"` to `"@opencode/plugin": "*"`
- Edit `tests/test_plugin_scaffold.py`:
  - Update assertions that check for `"@opencode-ai/plugin"` → `"@opencode/plugin"`
  - Update assertion that checks for `"PipelineEnforcement"` → `"pipeline-enforcement"` (id)
    or `"Plugin.define"` (entrypoint shape)
  - Update assertion that checks for `"tool.execute.before"` string →
    `"execute.before"` (new hook registration form)
  - Update docstrings and module header to reflect V2 migration
- Update docstrings and module headers in every file changed.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `plugins/pipeline-enforcement.ts` contains `export default Plugin.define`
- `plugins/pipeline-enforcement.ts` imports from `"@opencode/plugin"` (no `-ai`)
- `plugins/pipeline-enforcement.ts` does NOT contain the old named export
  `export const PipelineEnforcement`
- `plugins/package.json` declares `"@opencode/plugin"` (no `-ai`)
- `plugins/package.json` does NOT declare `"@opencode-ai/plugin"`
- All tests in `tests/test_plugin_scaffold.py` pass
- No other test file is broken by this change
- `pytest` exits 0

## Test criteria (must exist BEFORE implementation)

- `tests/test_plugin_scaffold.py::test_plugin_file_exists` — plugins/pipeline-enforcement.ts
  exists (unchanged, still passes)
- `tests/test_plugin_scaffold.py::test_package_json_exists` — plugins/package.json contains
  `@opencode/plugin` (updated from `@opencode-ai/plugin`)
- `tests/test_plugin_scaffold.py::test_plugin_exports_default_define` — file contains
  `Plugin.define` and `export default` (replaces old named-export test)
- `tests/test_plugin_scaffold.py::test_plugin_has_tool_hook` — file contains
  `execute.before` (updated from `tool.execute.before` string literal)
