# Story 23-02 — Migrate rtk.ts to OpenCode V2 Plugin API

Status: Planned
Feature: plugin-v2-migration (F-023)

## Context / Purpose

`plugins/rtk.ts` was written for OpenCode V1. Since the upgrade to V2 it fails to load at every
startup with `SchemaError(Missing key at ["default"])` — the rtk token-saving rewrite is
inactive on every bash command.

The plugin's job: before each bash tool call, run `rtk rewrite <command>` and replace the
command string with the rewritten version if rtk produces a different output. It gracefully
disables itself when `rtk` is not found in PATH.

The V1 entrypoint uses:
- Named export `RtkOpenCodePlugin` of type `Plugin` from `@opencode-ai/plugin`
- The Bun shell helper `$` from the plugin context for `which rtk` and `rtk rewrite`
- Returned hook object with `"tool.execute.before"` key

V2 requires `export default Plugin.define({ id, async setup(ctx) })`. The `$` Bun shell helper
is no longer provided via plugin context — process execution must use the standard Node.js
`child_process` module or the `Bun.spawn` API directly.

This story is independent of 23-01 and can be implemented in parallel.

## Requirements

- `plugins/rtk.ts` exports a V2 plugin as `export default Plugin.define({...})`
  with a stable `id: "rtk"`.
- The plugin imports from `@opencode/plugin` (not `@opencode-ai/plugin`).
- Functional behavior is identical to V1:
  - On `tool.execute.before` for `bash`/`shell` tools: run `rtk rewrite <command>`,
    replace `event.input.command` with rewritten value if it differs.
  - If `rtk` binary is not in PATH: log a warning and skip rewriting (plugin remains loaded).
- Process execution (replacing `$`) uses `child_process.execSync` or equivalent — no external
  runtime dependency beyond Node.js builtins.
- The plugin loads without error in V2 (no `SchemaError` in server log).

## Developer Targets (exactly, no more / no less)

- Edit `plugins/rtk.ts`:
  - Change import to `import { Plugin } from "@opencode/plugin"`
  - Replace named export with `export default Plugin.define({ id: "rtk", async setup(ctx) { ... } })`
  - Replace `$\`which rtk\`.quiet()` with a Node.js `child_process`-based PATH check
    (e.g. `execSync("where rtk", ...)` on Windows / `which rtk` on Unix, or cross-platform
    via `execSync` with `stdio: "ignore"` and a try/catch)
  - Replace `$\`rtk rewrite ${command}\`.quiet().nothrow()` with `execSync("rtk rewrite " + command)`
    wrapped in try/catch (return original command on error)
  - Register hook via `ctx.tool.hook("execute.before", async (event) => { ... })`
  - Access command via `(event.input as { command?: string }).command` (replaces `output.args`)
  - Mutate command via `(event.input as Record<string, unknown>).command = rewritten`
  - Add `import { execSync } from "child_process"` at top of file
  - Update module header docstring to describe V2 migration and removed `$` dependency
- Create `tests/test_rtk_plugin.py`:
  - `test_rtk_plugin_file_exists` — plugins/rtk.ts exists
  - `test_rtk_uses_v2_entrypoint` — file contains `Plugin.define` and `export default`
  - `test_rtk_imports_v2_package` — file contains `@opencode/plugin` (no `-ai`)
  - `test_rtk_uses_child_process` — file contains `child_process` or `execSync`
  - `test_rtk_does_not_use_bun_shell` — file does NOT contain `$\`` (Bun shell template literal)
  - `test_rtk_has_tool_hook` — file contains `execute.before`

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `plugins/rtk.ts` contains `export default Plugin.define`
- `plugins/rtk.ts` imports from `"@opencode/plugin"` (no `-ai`)
- `plugins/rtk.ts` does NOT contain Bun shell template literals (`` $` ``)
- `plugins/rtk.ts` uses `child_process` for process execution
- All tests in `tests/test_rtk_plugin.py` pass
- No existing test file is broken by this change
- `pytest` exits 0

## Test criteria (must exist BEFORE implementation)

- `tests/test_rtk_plugin.py::test_rtk_plugin_file_exists` — plugins/rtk.ts exists
- `tests/test_rtk_plugin.py::test_rtk_uses_v2_entrypoint` — file contains `Plugin.define`
  and `export default`
- `tests/test_rtk_plugin.py::test_rtk_imports_v2_package` — file contains `@opencode/plugin`
- `tests/test_rtk_plugin.py::test_rtk_uses_child_process` — file contains `child_process`
  or `execSync`
- `tests/test_rtk_plugin.py::test_rtk_does_not_use_bun_shell` — file does NOT contain `` $` ``
- `tests/test_rtk_plugin.py::test_rtk_has_tool_hook` — file contains `execute.before`
