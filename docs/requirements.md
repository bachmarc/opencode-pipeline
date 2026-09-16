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

## Non-functional requirements

- **NFR-001 Language:** Repo docs English; agent prompts stay German (they steer German
  dialogue); user dialogue German.
- **NFR-002 Zero infrastructure:** No server, no DB, no Docker for the checks — pytest +
  the repo's own files only.
- **NFR-003 Cheap verifiability:** All checks are deterministic file/bash assertions;
  a cheap model can evaluate the compressed pytest output.

## Out of scope

- Tests for opencode itself (upstream tool).
- Automatic deployment (push-to-live automation, systemd, etc.). Deployment stays manual:
  `git pull` in the live clone + restart.
- CI (GitHub Actions) — can be added later.