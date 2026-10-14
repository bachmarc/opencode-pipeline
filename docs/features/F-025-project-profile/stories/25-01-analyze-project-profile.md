# Story 25-01 — Analyze Project Profile (Test Command + Deploy Hints)

Status: Planned
Feature: Project Profile & QA Configuration (F-025)

## Context / Purpose

`analyze_project.py` is the first step of `/migrate`. It scans a project and returns a JSON analysis that all subsequent phases use. Today it detects the tech stack (python/ruby/java/javascript) but stops there — it does not detect the test command or any deployment signals.

This means `/migrate` Phase 2 has no basis for suggesting test commands or deploy methods to the user, `provision_structure.py` cannot write a `qa_config.json` with the right checker, and the Architect always starts the deploy-method dialog blind.

This story extends `analyze_project.py` to produce a `test_command` field (the most likely test runner for this stack) and a `deploy_hints` list (signals found in the project that indicate how it is deployed). It also adds `qa_checker` — the `qa_compress.py` checker name that maps to the detected test command — so downstream phases do not re-derive it.

## Requirements

`analyze_project.py` must return three new fields in its JSON output:

- `test_command` — the detected or inferred test command string (e.g. `"pytest"`, `"bundle exec rspec"`, `"go test ./..."`, `"npm test"`, `"./gradlew test"`, `"mvn test"`, `"unknown"`).
- `qa_checker` — the `qa_compress.py` checker name matching the test command (e.g. `"pytest"`, `"rspec"`, `"jest"`, `"gradle"`, `"maven"`, `"unknown"`).
- `deploy_hints` — a list of zero or more strings describing deployment signals found (e.g. `"github-actions"`, `"dockerfile"`, `"makefile-deploy-target"`, `"scp-script"`, `"heroku"`, `"unknown"`).

Detection rules for `test_command` / `qa_checker` (highest-priority match wins):

| Marker found | `test_command` | `qa_checker` |
|---|---|---|
| `Gemfile` | `bundle exec rspec` | `rspec` |
| `package.json` | `npm test` | `jest` |
| `pom.xml` | `mvn test` | `maven` |
| `build.gradle` or `build.gradle.kts` | `./gradlew test` | `gradle` |
| `requirements.txt` / `pyproject.toml` / `setup.py` | `pytest` | `pytest` |
| none of the above | `unknown` | `unknown` |

Detection rules for `deploy_hints`:

| Signal | Hint string |
|---|---|
| `.github/workflows/` directory exists | `"github-actions"` |
| `Dockerfile` or `docker-compose.yml` exists | `"dockerfile"` |
| `Makefile` with a `deploy` target | `"makefile-deploy-target"` |
| `Procfile` exists | `"heroku"` |
| Any `*.sh` file whose name contains `deploy` or `scp` | `"scp-script"` |
| None of the above | `"unknown"` |

Multiple deploy hints are allowed (e.g. both `"github-actions"` and `"dockerfile"`). If none match, return `["unknown"]`.

The existing output fields (`project_name`, `stack`, `agent_file`, `structure`, `git`, `missing`, `existing_pipeline_files`) must remain unchanged.

## Developer Targets (exactly, no more / no less)

- `scripts/analyze_project.py` — add `detect_test_command(target: Path) -> tuple[str, str]` returning `(test_command, qa_checker)`; add `detect_deploy_hints(target: Path) -> list[str]`; extend `analyze_project()` return dict with `test_command`, `qa_checker`, `deploy_hints`. Update module docstring.
- `tests/test_analyze_project.py` — add tests for all detection cases (one test per stack marker, one per deploy hint signal, one for "unknown" fallback for both). Tests written first (red before implementation).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `analyze_project()` returns `test_command`, `qa_checker`, `deploy_hints` for all inputs.
- All stack → test_command mappings from the table above are correct.
- All deploy hint signals from the table above are detected.
- Unknown stack → `test_command="unknown"`, `qa_checker="unknown"`.
- No deploy signals → `deploy_hints=["unknown"]`.
- Multiple deploy signals → multiple entries in `deploy_hints`.
- Existing output fields unchanged (no regression on existing tests).
- `tests/test_analyze_project.py` has at least one test per detection rule row.

## Test criteria (must exist BEFORE implementation)

- `tests/test_analyze_project.py::test_detect_test_command_python` — project with `requirements.txt` → `test_command="pytest"`, `qa_checker="pytest"`
- `tests/test_analyze_project.py::test_detect_test_command_ruby` — project with `Gemfile` → `test_command="bundle exec rspec"`, `qa_checker="rspec"`
- `tests/test_analyze_project.py::test_detect_test_command_node` — project with `package.json` → `test_command="npm test"`, `qa_checker="jest"`
- `tests/test_analyze_project.py::test_detect_test_command_maven` — project with `pom.xml` → `test_command="mvn test"`, `qa_checker="maven"`
- `tests/test_analyze_project.py::test_detect_test_command_gradle` — project with `build.gradle` → `test_command="./gradlew test"`, `qa_checker="gradle"`
- `tests/test_analyze_project.py::test_detect_test_command_unknown` — empty project → `test_command="unknown"`, `qa_checker="unknown"`
- `tests/test_analyze_project.py::test_deploy_hints_github_actions` — project with `.github/workflows/` → `"github-actions"` in hints
- `tests/test_analyze_project.py::test_deploy_hints_dockerfile` — project with `Dockerfile` → `"dockerfile"` in hints
- `tests/test_analyze_project.py::test_deploy_hints_makefile_target` — project with `Makefile` containing `deploy:` → `"makefile-deploy-target"` in hints
- `tests/test_analyze_project.py::test_deploy_hints_heroku` — project with `Procfile` → `"heroku"` in hints
- `tests/test_analyze_project.py::test_deploy_hints_scp_script` — project with `deploy.sh` → `"scp-script"` in hints
- `tests/test_analyze_project.py::test_deploy_hints_multiple` — project with both `Dockerfile` and `.github/workflows/` → both hints present
- `tests/test_analyze_project.py::test_deploy_hints_unknown` — project with no deploy signals → `deploy_hints=["unknown"]`
- `tests/test_analyze_project.py::test_existing_fields_unchanged` — existing fields still present after extension
