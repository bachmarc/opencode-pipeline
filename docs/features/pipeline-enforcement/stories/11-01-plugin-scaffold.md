# Story 11-01 — Plugin Scaffold and Infrastructure

Status: Planned
Feature: pipeline-enforcement (F-007)

## Context / Purpose

The opencode-pipeline repo is currently pure Python/Bash/Markdown. To build an opencode plugin,
we need TypeScript infrastructure: a `plugins/` directory, a `package.json` for the
`@opencode-ai/plugin` dependency, and a skeleton plugin file that opencode can load. This story
establishes the foundation — subsequent stories add individual guards.

The plugin must work when deployed to `~/.config/opencode/plugins/` via the release branch.
It must also be testable in the dev repo.

## Requirements

- `plugins/` directory exists at repo root with a `package.json` declaring `@opencode-ai/plugin`
  as dependency.
- `plugins/pipeline-enforcement.ts` exists as a valid opencode plugin that loads without error
  and exports a named plugin function.
- The plugin registers `tool.execute.before` hook but initially passes through all calls
  (no guards active yet — just the wiring).
- `.gitignore` updated to exclude `plugins/node_modules/`.
- Deployment path documented: `plugins/` → release → `~/.config/opencode/plugins/`.

## Developer Targets (exactly, no more / no less)

- Create `plugins/package.json` with `@opencode-ai/plugin` dependency
- Create `plugins/pipeline-enforcement.ts` with:
  - Named export `PipelineEnforcement` as `Plugin` type
  - `tool.execute.before` hook registered (pass-through, logs tool name)
  - Guard registry pattern: empty `guards` array, iteration in hook
- Update `.gitignore`: add `plugins/node_modules/`
- Create `tests/test_plugin_scaffold.py`:
  - Test that `plugins/pipeline-enforcement.ts` exists
  - Test that `plugins/package.json` exists and contains `@opencode-ai/plugin`
  - Test that plugin file exports `PipelineEnforcement`
  - Test that plugin file contains `tool.execute.before`

## Acceptance criteria (checked by qa-manager)

- `plugins/pipeline-enforcement.ts` is valid TypeScript, exports `PipelineEnforcement`
- `plugins/package.json` declares `@opencode-ai/plugin` dependency
- `.gitignore` contains `plugins/node_modules`
- All tests in `tests/test_plugin_scaffold.py` pass
- No Python code changes outside tests

## Test criteria (must exist BEFORE implementation)

- `tests/test_plugin_scaffold.py::test_plugin_file_exists` — plugins/pipeline-enforcement.ts exists
- `tests/test_plugin_scaffold.py::test_package_json_exists` — plugins/package.json exists and has @opencode-ai/plugin
- `tests/test_plugin_scaffold.py::test_plugin_exports_named_function` — file contains "PipelineEnforcement"
- `tests/test_plugin_scaffold.py::test_plugin_has_tool_hook` — file contains "tool.execute.before"
