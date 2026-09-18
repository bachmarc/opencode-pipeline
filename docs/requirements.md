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
- **REQ-001a Release branch strategy:** `main` is the development line (features merge
  here after QA-PASS). A `release` branch holds the stable, deployable state. The live
  clone pulls `release`, not `main`. Promoting `main` → `release` is a conscious step
  when a milestone is reached — not automatic after every merge.
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

- **REQ-008 Workflow documentation:** The README contains a step-by-step explanation of
  how the pipeline workflow operates in practice: the interactive design dialogue
  (User ↔ Architect), the story-driven planning checkpoint, the autonomous Dev+QA
  execution, and the escalation paths (FAIL loops, BLOCKED_Design, BLOCKED_Requirements).
  Includes a Mermaid flowchart visualizing the full agent interaction.

- **REQ-009 Feature → Story hierarchy:** The flat `STORIES.md` table is replaced by a
  hierarchical structure: `docs/features/<feature-name>/` contains a `feature.md` (scope,
  status, traceability) and a `stories/` sub-directory with individual story files. A
  top-level index (`FEATURES.md` or equivalent) lists all features with status. Features
  are the grouping unit above stories; their status is derived from their stories' statuses.
  The structure must be human-readable (browsable on GitHub) and machine-optimized (agents
  can resolve feature/story state by reading predictable file paths).

- **REQ-010 Multi-user feature isolation:** Multiple users can work on different features
  simultaneously in separate opencode sessions, connected via GitHub. Each feature is the
  work unit per user/session. A **deterministic claim mechanism** (Python script, not LLM
  free-hand) prevents two sessions from working on the same feature:
  - A feature's status file tracks `status: in-progress (user@host, timestamp)`.
  - A corresponding `feature/<name>` branch signals the claim at Git level.
  - Claiming, releasing, and stale-claim detection are handled by
    `scripts/feature_claim.py` with atomic pull-check-commit-push and proper exit codes.
  - LLM agents call the script and react to exit codes; they never manage claims directly.

- **REQ-011 Session resilience / recovery:** When a session crashes, tokens run out, or
  connectivity is lost, the pipeline must support a defined re-entry path:
  1. **Intent tracking:** Before starting an action, the responsible agent writes the
     current intent to `.pipeline/intent.json` (story ID, agent role, next step, timestamp).
     On completion the intent is marked done. An open (not-done) intent is the re-entry
     point for the next session.
  2. **Automatic state scan at session start:** A deterministic script
     (`scripts/session_recovery.py`) runs at the beginning of a new session and collects:
     - Open intents from `.pipeline/intent.json`
     - Existing worktrees (`.worktrees/`), their branches, uncommitted/staged changes,
       merge conflicts, detached HEAD
     - Git state on main (ahead/behind remote, dirty working tree)
     - QA state (last verdict, FAIL-loop count) from `.pipeline/qa-state/`
     - Feature claim status
  3. **Proactive reporting:** The agent presents the recovery summary to the user
     immediately — not on request, not after the user asks to check logs.
  The recovery script is deterministic; the LLM only interprets and acts on its output.

- **REQ-012 Documenter agent:** A new `documenter` agent role on the cheap model maintains
  documentation consistency across the project:
  - **Trigger:** Automatically after QA-PASS and before merge (triggered by QA-Manager),
    plus manually via `/document` command.
  - **Input:** Git-diff based — receives the diff of what changed, current `docs/`, and
    affected source files; reconciles documentation against actual state.
  - **Scope:** README updates, design-doc consistency (decisions made in chat reflected in
    `docs/design.md`), class/method descriptions, docstrings in changed files, removal of
    stale comments. Does NOT invent new architecture — relies on Architect/Developer/QA
    having done their work and synthesizes what exists.
  - **Cost model:** Runs on the locally configured cheap model
    (`agent.documenter.model` in `opencode.jsonc`).

- **REQ-013 Deterministic pipeline scripts:** Tasks that are currently handled free-hand by
  LLM agents but require determinism are moved to scripts (`scripts/`). Agents call these
  scripts and interpret their output; they do not perform the underlying operations
  directly. Priority targets (high → low):
  1. **Worktree/branch setup** (`scripts/worktree_setup.py`): Validate story ID, derive
     slug deterministically, create worktree + branch atomically, verify main is clean.
  2. **Pipeline status aggregation** (`scripts/pipeline_status.py`): Parse STORIES.md /
     feature files, correlate with branches, worktrees, pytest results, QA state. Output
     machine-readable JSON.
  3. **Project scaffolding** (`scripts/scaffold_project.py`): Create project structure
     deterministically — `cp` templates instead of LLM re-generation, only placeholder
     fill remains with the LLM.
  4. **Architecture check** (extension to `qa_compress.sh`): AST-based import validation
     for `src/core/` zero-import rule, fake-interface parity check.
  5. **Commit metadata** (`scripts/prepare_commit_metadata.py`): Extract changed symbols
     via diff, find dependents via import-graph, embed pytest result, format deterministically.
  6. **Story ID resolution** (`scripts/resolve_story.py`): Normalize input (ID, slug,
     branch name), look up story file, return JSON with all metadata.
  7. **Story status mutation** (`scripts/story_status.py`): Update status in feature/story
     files with standardized labels, no other lines touched.
  8. **QA verdict routing** (`scripts/qa_route.py` + `.pipeline/qa-state/`): Persist
     verdict history, track FAIL-loop and design-fix counters, enforce budget limits,
     output next agent + context as JSON.
  9. **Merge validation** (`scripts/merge_if_passed.py`): Only merge if QA-PASS recorded
     in `.pipeline/qa-state/` for exactly this branch.
  10. **Story creation** (`scripts/create_story.py`): Determine next free ID, `cp` template,
      fill machine fields, insert row into feature index.
  11. **Template constancy check** (`scripts/check_template_constancy.py`): Compare constant
      sections of a project's AGENTS.md against `templates/AGENTS.md` — registerable in
      `qa_compress.sh`.

## Non-functional requirements

- **NFR-001 Language:** All portable files (agent prompts, commands, templates, scripts,
  repo docs) are English. User dialogue language is configured per project in `AGENTS.md`
  (default: respond in the user's language). Code identifiers are English.
- **NFR-002 Zero infrastructure:** No server, no DB, no Docker for the checks — pytest +
  the repo's own files only.
- **NFR-003 Cheap verifiability:** All checks are deterministic file/bash assertions;
  a cheap model can evaluate the compressed pytest output.
- **NFR-004 LLM ↔ Script boundary:** LLM agents are responsible for reasoning, dialogue,
  and creative decisions (requirements, design, code logic). All operations that require
  atomicity, state persistence, format consistency, or concurrency safety are handled by
  deterministic scripts. Agents call scripts and interpret results; they never perform
  these operations free-hand.

- **REQ-014 README restructure (end-user documentation):** The README is restructured
  from inside-out (folder table → design decisions → installation) to a user-oriented
  flow for opencode users new to multi-agent setups:
  1. **Intro/Pitch** (ausführlich): What the framework does for developers, the four
     agent roles, repo contents woven into prose (not isolated table), key design
     principles as bullet points.
  2. **Development process**: Mermaid flowchart (prominent), Phase 1 (design dialogue),
     Phase 2 (user-go checkpoint), Phase 3 (autonomous dev+QA), escalation paths,
     command quick-reference table.
  3. **Installation**: Two scenarios — (a) fresh install via `git clone` and (b)
     adding the framework to an existing `~/.config/opencode` via `git init` + remote
     add + pull (preserving local files like `opencode.jsonc`). Local config setup.
     Forward-links to technical details.
  4. **Technical Details** (reference, linked from above): model assignment mechanics,
     Phase-0 enforcement, agent detail table, deployment/branching/promotion/rollback,
     qa_compress.sh extension, per-project AGENTS.md, architecture pattern
     (function vs. connectivity).
  5. **Open points / outlook** (brief).
  Content is also editorially revised (not just reordered): tightened, improved, and
  adapted to the target audience (opencode users new to agents).

## Out of scope

- Tests for opencode itself (upstream tool).
- Automatic deployment (push-to-live automation, systemd, etc.). Deployment stays manual:
  `git pull` in the live clone + restart.
- CI (GitHub Actions) — can be added later.
- Real-time collaboration (live co-editing). Multi-user works via Git push/pull, not
  live sync.