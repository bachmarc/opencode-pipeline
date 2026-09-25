# Story 17-01 — Plugin-Relative Script Paths (fail-closed)

Status: Planned
Feature: F-013-framework-path-consolidation (F-013)

## Context / Purpose

The `session-recovery-guard.ts` currently checks `${directory}/scripts/session_recovery.py`
(project-relative). In any project that is not the dogfood repo, this path does not exist →
the guard silently skips (fail-open). The guard must instead resolve the script from the
framework installation, which is always at `../scripts/` relative to the plugin file itself.

The plugin lives in `~/.config/opencode/plugins/`. The scripts live in
`~/.config/opencode/scripts/`. Using `import.meta.dirname` (available in Bun/ESM) gives the
plugin's own directory — from there `../scripts/` is the framework scripts directory,
platform-independently (Windows and Unix).

If the script is not found at the resolved path, the guard must throw a clear error
("Framework not installed") instead of silently skipping.

## Requirements

- All guards that invoke framework scripts resolve the script path via
  `join(import.meta.dirname, "..", "scripts", "<script-name>")`.
- `session-recovery-guard.ts`: if the resolved `session_recovery.py` path does not exist →
  throw `"Framework not installed: session_recovery.py not found at <path>. Reinstall opencode-pipeline."` (fail-closed).
- The guard no longer checks `${directory}/scripts/session_recovery.py` at all.
- The shell invocation uses the absolute resolved path, not a relative `scripts/…` string.
- All other guards that reference framework scripts (if any) are updated the same way.

## Developer Targets (exactly, no more / no less)

- `plugins/guards/session-recovery-guard.ts` — replace `${directory}/scripts/session_recovery.py`
  check with `join(import.meta.dirname, "..", "scripts", "session_recovery.py")`;
  fail-closed if not found (throw "Framework not installed: …"); use absolute path in shell
  invocation. Update module docstring to describe the new resolution strategy.
- `tests/test_plugin_path_resolution.py` — new test file: reads
  `plugins/guards/session-recovery-guard.ts` as text and asserts via regex:
  (1) `import\.meta\.dirname` is present; (2) `\$\{directory\}/scripts/` is absent;
  (3) `Framework not installed` is present in the error message string.

## Acceptance criteria (checked by qa-manager)

- `session-recovery-guard.ts` contains no `${directory}/scripts/` reference.
- `session-recovery-guard.ts` contains `import.meta.dirname`.
- `session-recovery-guard.ts` contains the string "Framework not installed".
- All tests pass.

## Test criteria (must exist BEFORE implementation)

- `tests/test_plugin_path_resolution.py::test_uses_import_meta_dirname` — read
  `plugins/guards/session-recovery-guard.ts`, assert `import.meta.dirname` present.
- `tests/test_plugin_path_resolution.py::test_no_directory_scripts_reference` — assert
  `${directory}/scripts/` absent from the file.
- `tests/test_plugin_path_resolution.py::test_framework_not_installed_message` — assert
  string "Framework not installed" present in the file.
- Existing guard tests remain green.
