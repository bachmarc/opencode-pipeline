# Requirements — opencode-pipeline Dev Repo

**Status:** Derived summary generated from features and stories · **Purpose:** Quick-start overview for the Architect

This document is a **derived summary** generated from the feature and story hierarchy. It provides a high-level overview of the project scope, features, and non-functional requirements. For detailed context, requirements, and acceptance criteria, refer to the individual feature and story files in `docs/features/`.

## Feature Overview

The opencode-pipeline project is organized into 7 features, each representing a major capability or phase:

| Feature ID | Title | Vision (1-line) | Status | Stories |
|---|---|---|---|---|
| F-RETRO | Retroactive Traceability | Pre-pipeline changes documented retroactively | Done | RETRO-01 through RETRO-05 |
| F-001 | Foundation | Repository structure, docs, self-checks, deployment, versioning | Done | 01-01 through 01-05 |
| F-002 | Internationalization (English) | Portable files in English, dialogue language decoupled | Done | 04-01 through 04-04 |
| F-003 | Documentation | README restructured for user orientation and workflow guidance | In-progress | 05-01, 07-01 |
| F-004 | Pipeline Evolution | Deterministic scripts, session recovery, multi-user support, documenter agent | Planned | 06-01 through 06-08 |
| F-005 | Documentation Model Reform | Features/stories as primary source, requirements/design as derived summaries | Done | 02-01 through 02-04 |
| F-006 | Documentation Model Migration | Migrate all repo data to new documentation model | Planned | 09-01 through 09-06 |

## Functional Requirements (by Feature)

### F-RETRO: Retroactive Traceability
- Changes made directly to the repository before the pipeline existed are documented retroactively
- All foundational changes (model de-hardwiring, role abstraction, Phase-0 enforcement, templates, README) are captured in project history

### F-001: Foundation
- **Two-clone topology:** Development in dev clone (`~/Development/opencode-pipeline`), live clone (`~/.config/opencode`) is read-only (pull + restart)
- **Release branch strategy:** `main` is development line, `release` is stable/deployable; live clone pulls `release`
- **Self-checks:** Deterministic pytest checks validate repo invariants (frontmatter, no model names in portable files, no runner names in portable prompts, template constancy, script syntax)
- **Deploy procedure:** Documented procedure to pull QA-passed changes from dev repo to live clone
- **Template constancy:** `templates/AGENTS.md` constant sections are the binding framework-project interface
- **Versioning:** `APP_VERSION` tracked for releases

### F-002: Internationalization (English)
- All portable files (`agent/`, `command/`, `templates/`, `scripts/`) are written in English
- Portable prompts (`agent/*.md`, `command/*.md`) are runner-agnostic: they reference "the configured test suite / configured checkers" instead of concrete runner names; enforced by the invariant test `tests/test_no_runner_names_in_prompts.py` (see story 12-07-prompt-genericization)
- Dialogue language is decoupled from code/identifier language and configured per project in `AGENTS.md`
- Framework default: respond in the user's language

### F-003: Documentation
- README restructured from inside-out to user-oriented flow: pitch → process → install → reference
- Workflow explanation with Mermaid flowchart, phase descriptions, escalation paths, command quick-reference
- Installation guidance for fresh install and existing setup scenarios
- Technical details as reference sections with forward-links

### F-004: Pipeline Evolution
- **Feature → Story hierarchy:** `docs/features/<feature-name>/` with `feature.md` and `stories/` subdirectory
- **Multi-user feature isolation:** Deterministic claim mechanism (`scripts/feature_claim.py`) prevents concurrent work on same feature
- **Session resilience / recovery:** Intent tracking (`.pipeline/intent.json`) and recovery script (`scripts/session_recovery.py`) for crash/disconnect re-entry
- **Documenter agent:** New role on cheap model maintains documentation consistency after QA-PASS and on manual `/document` command
- **Deterministic pipeline scripts:** 11 scripts handle worktree setup, status aggregation, scaffolding, commit metadata, story management, QA routing, merge validation, etc.

### F-005: Documentation Model Reform
- Features become primary source of truth with their own vision and context
- Stories become self-contained with purpose, requirements, and acceptance criteria
- Documenter generates/updates `requirements.md` and `design.md` as derived summaries with feature/story references

### F-006: Documentation Model Migration
- Migrate 5 feature.md files to new format (Vision + Context, drop req: field)
- Migrate 22 story files to new 5-section format (Feature: instead of Traceability:)
- Migrate story indexes (STORIES.md → FEATURES.md)
- Rewrite requirements.md and design.md as Documenter-style summaries
- Update commands, prompts, templates, scripts, and tests to reference new model

## Non-Functional Requirements

- **NFR-001 Language:** All portable files (agent prompts, commands, templates, scripts, repo docs) are English. User dialogue language is configured per project in `AGENTS.md` (default: respond in the user's language). Code identifiers are English.
- **NFR-002 Zero infrastructure:** No server, no DB, no Docker for the checks — pytest + the repo's own files only.
- **NFR-003 Cheap verifiability:** All checks are deterministic file/bash assertions; a cheap model can evaluate the compressed pytest output.
- **NFR-004 LLM ↔ Script boundary:** LLM agents are responsible for reasoning, dialogue, and creative decisions. All operations requiring atomicity, state persistence, format consistency, or concurrency safety are handled by deterministic scripts. Agents call scripts and interpret results; they never perform these operations free-hand.

## Out of Scope

- Tests for opencode itself (upstream tool)
- Automatic deployment (push-to-live automation, systemd, etc.). Deployment stays manual: `git pull` in the live clone + restart
- CI (GitHub Actions) — can be added later
- Real-time collaboration (live co-editing). Multi-user works via Git push/pull, not live sync
