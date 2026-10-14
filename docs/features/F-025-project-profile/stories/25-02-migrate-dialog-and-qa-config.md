# Story 25-02 — Migrate Dialog: Test+Deploy Config and qa_config.json

Status: Planned
Feature: Project Profile & QA Configuration (F-025)

## Context / Purpose

After `analyze_project.py` produces a project profile (story 25-01), the `/migrate` skill Phase 2 presents the analysis to the user and asks for confirmation. Today this confirmation covers stack and branch name — but never asks about the test command or deployment method. Phase 4 (`provision_structure.py`) creates directories but never writes `qa_config.json`, so `qa_compress.py` falls back to pytest for every project regardless of language.

This story closes the loop: Phase 2 of the migrate skill gains a test+deploy dialog, `provision_structure.py` writes `qa_config.json` using the confirmed checker, and `validate_migration.py` gains a deploy-documentation check. After this story, every migrated project has a valid `qa_config.json` and a documented deploy method in `AGENTS.md`.

The deploy method is not enforced or executed by the pipeline — it is documented so the Architect can offer it as context when the user asks "how do I ship this?".

## Requirements

**`skills/migrate-project.md` Phase 2 dialog extension:**

After the existing stack/branch confirmation, the Architect must ask two additional questions:

1. **Test command confirmation** — present the detected `test_command` from the analysis and ask: "Is this the correct test command for your project?" Options: confirm / correct it / "I'll configure manually later". If corrected, record the new command and derive the `qa_checker` from it (using the same mapping as 25-01; unknown commands → `qa_checker="unknown"`).

2. **Deploy method** — present the detected `deploy_hints` and ask: "How is this project deployed?" The user selects one or more from: `git-push`, `scp`, `docker`, `ci-cd`, `mcp`, `manual`, `other` — plus free text for "other". The confirmed deploy method(s) are stored for use in Phase 4.

**`scripts/provision_structure.py` extension:**

Accept an optional `qa_checker` argument (string) and `deploy_methods` argument (list of strings). When `qa_checker` is provided and not `"unknown"`:
- Write `qa_config.json` in the project root: `{"checkers": ["<qa_checker>"]}`.
- Never overwrite an existing `qa_config.json`.

When `deploy_methods` is provided:
- Append a `## Deployment` section to `AGENTS.md` (if it exists) documenting the methods. Never overwrite existing `## Deployment` sections.

Report written/skipped files in the existing report dict under new keys `"qa_config"` and `"deploy_section"`.

**`scripts/validate_migration.py` extension:**

Add two new checks:
- `check_deploy_documented` — passes if `AGENTS.md` contains a `## Deployment` section with non-placeholder content. Fails with "AGENTS.md missing ## Deployment section".
- `check_qa_config` already exists — extend it to also pass when `qa_checker="unknown"` and `qa_config.json` has `{"checkers": []}` (explicit opt-out is valid).

**`skills/migrate-project.md` Phase 4 update:**

Document that `provision_structure.py` now accepts `qa_checker` and `deploy_methods` parameters and must be called with the confirmed values from Phase 2.

## Developer Targets (exactly, no more / no less)

- `skills/migrate-project.md` — extend Phase 2 with test-command and deploy-method dialog blocks; extend Phase 4 to pass `qa_checker` and `deploy_methods` to `provision_structure.py`. Update skill docstring/header comment.
- `scripts/provision_structure.py` — add optional `qa_checker: str = ""` and `deploy_methods: list[str] = []` parameters to `provision_structure()`; implement `qa_config.json` writing; implement `## Deployment` section append to `AGENTS.md`; add `"qa_config"` and `"deploy_section"` keys to report dict. Update module docstring.
- `scripts/validate_migration.py` — add `check_deploy_documented(target_path: Path) -> Dict` function; register it in `validate_migration()`; extend `check_qa_config` to accept explicit opt-out. Update module docstring.
- `tests/test_provision_structure.py` — add tests for `qa_config.json` writing, no-overwrite, deploy section append, no-overwrite of existing section, unknown checker → no file written.
- `tests/test_validate_migration.py` — add tests for `check_deploy_documented` pass/fail; test explicit opt-out `qa_config.json` passes.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `skills/migrate-project.md` Phase 2 contains a test-command confirmation dialog and a deploy-method dialog.
- `skills/migrate-project.md` Phase 4 passes `qa_checker` and `deploy_methods` to `provision_structure.py`.
- `provision_structure()` writes `qa_config.json` when `qa_checker` is a known checker name.
- `provision_structure()` does NOT write `qa_config.json` when `qa_checker="unknown"`.
- `provision_structure()` does NOT overwrite an existing `qa_config.json`.
- `provision_structure()` appends `## Deployment` to `AGENTS.md` when `deploy_methods` is non-empty.
- `provision_structure()` does NOT overwrite an existing `## Deployment` section.
- `validate_migration.py` `check_deploy_documented` passes when `## Deployment` exists with real content.
- `validate_migration.py` `check_deploy_documented` fails when section is absent.
- `validate_migration.py` `check_qa_config` passes for `{"checkers": []}` (explicit opt-out).
- All existing tests still pass (no regression).

## Test criteria (must exist BEFORE implementation)

- `tests/test_provision_structure.py::test_writes_qa_config_for_known_checker` — known checker → `qa_config.json` written with correct content
- `tests/test_provision_structure.py::test_no_qa_config_for_unknown_checker` — `qa_checker="unknown"` → no `qa_config.json` created
- `tests/test_provision_structure.py::test_does_not_overwrite_existing_qa_config` — existing `qa_config.json` → not overwritten, reported as skipped
- `tests/test_provision_structure.py::test_appends_deploy_section_to_agents_md` — `deploy_methods=["docker"]` + existing `AGENTS.md` → `## Deployment` section appended
- `tests/test_provision_structure.py::test_does_not_overwrite_existing_deploy_section` — `AGENTS.md` with `## Deployment` already present → not overwritten
- `tests/test_provision_structure.py::test_report_contains_qa_config_and_deploy_keys` — report dict has `"qa_config"` and `"deploy_section"` keys
- `tests/test_validate_migration.py::test_check_deploy_documented_pass` — `AGENTS.md` with `## Deployment` + real content → pass
- `tests/test_validate_migration.py::test_check_deploy_documented_fail_missing` — no `## Deployment` section → fail
- `tests/test_validate_migration.py::test_qa_config_explicit_optout_passes` — `{"checkers": []}` → check_qa_config passes
