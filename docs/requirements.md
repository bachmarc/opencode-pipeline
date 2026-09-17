# Requirements — opencode-pipeline Dev Repo

**Status:** Draft for review · **Author:** architect · REQ-IDs are the traceability anchors for stories.

## Problem

The pipeline repo (agent roles, skill, commands, qa_compress.sh, templates) was developed
directly in the live clone `~/.config/opencode`: no stories, no QA gate, no dogfooding.
The framework that demands "stories → branch → QA gate" never applied that to itself.
Model assignments were hardcoded; the Phase-0 checkpoint existed only in prose.

## Goal group

The opencode agent framework shall be developed like any project the pipeline builds:
dogfooded (stories, branches, deterministic self-checks, QA gate), with a clean separation
between development and deployment (two-clone topology), and locally configurable model
assignments.

## Functional requirements

- **REQ-001 Two-clone topology:** Development happens in a dev clone
  (`/mnt/content_main/Development/opencode-pipeline`). The live clone `~/.config/opencode`
  is read-only (pull + restart). This rule is documented and enforced by repo convention.
- **REQ-002 Retro traceability:** The changes already made directly (model de-hardwiring,
  role abstraction, permission.task enforcement, AGENTS.md template, README rework) are
  documented retroactively as stories in `STORIES.md` (marked "retro").
- **REQ-003 Framework self-checks:** Deterministic pytest checks exist that validate the
  repo's own invariants: agent frontmatter intact (no `model:` line, valid fields), no
  concrete model/provider names in portable files, `templates/AGENTS.md` exists and contains
  the constant sections, `scripts/qa_compress.sh` passes `bash -n`.
- **REQ-004 QA-barability:** The self-checks are pytest-based so `qa_compress.sh` can
  compress their output — the QA gate becomes applicable to this repo.
- **REQ-005 Deploy procedure:** A documented procedure (and optionally a command) to pull
  QA-passed changes from the dev repo into the live clone, including the opencode restart
  requirement (config is not hot-reloaded).
- **REQ-006 Template constancy:** `templates/AGENTS.md` constant sections (workflow, git
  conventions, languages, prohibitions) are the binding framework-project interface; changes
  to them require explicit user approval in the planning checkpoint.
- **REQ-007 English-first portable files:** All portable files (`agent/`, `command/`,
  `templates/`, `scripts/`) are written in English. This includes agent prompts, command
  descriptions, template content, section headers, and inline comments. User dialogue
  language is not hardcoded — it is configured per project in the project's `AGENTS.md`
  (section "Languages"). The framework default is: respond in the user's language.

## Non-functional requirements

- **NFR-001 Language:** All portable files (agent prompts, commands, templates, scripts,
  repo docs) are English. User dialogue language is configured per project in `AGENTS.md`
  (default: respond in the user's language). Code identifiers are English.
- **NFR-002 Zero infrastructure:** No server, no DB, no Docker for the checks — pytest +
  the repo's own files only.
- **NFR-003 Cheap verifiability:** All checks are deterministic file/bash assertions;
  a cheap model can evaluate the compressed pytest output.

## Out of scope

- Tests for opencode itself (upstream tool).
- Automatic deployment (push-to-live automation, systemd, etc.). Deployment stays manual:
  `git pull` in the live clone + restart.
- CI (GitHub Actions) — can be added later.