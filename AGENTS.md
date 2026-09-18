# AGENTS.md — opencode-pipeline (Dev Repo)

> Skeleton filled from `~/.config/opencode/templates/AGENTS.md`. Constant sections (workflow, git
> conventions, languages, prohibitions) kept unchanged; project-specifics filled in dialogue.

## This project: opencode-pipeline — multi-agent dev pipeline as config-as-code

- **What:** The opencode agent framework (architect / developer / qa-manager roles, dev-workflow
  skill, commands, qa_compress.sh). Developed dogfooded: this pipeline repo is itself developed
  through the pipeline (stories → branches → QA gate).
- **Stack:** Markdown (agents, skills, commands, docs), Bash (`scripts/qa_compress.sh`),
  Python 3 + pytest (framework self-checks in `tests/`), Git. No runtime app.
- **Versioning:** `APP_VERSION = "0.1.0"` — bump on notable merges (document in STORIES.md).

## Core rules (source of truth: `docs/requirements.md` + `docs/design.md`)

- **Two-clone topology:** Development happens HERE (`~/Development/opencode-pipeline`).
  `~/.config/opencode` is the LIVE clone — **read-only**: `git pull release` + opencode restart only.
  Never develop in the live clone. Never edit files in `~/.config/opencode` directly.
  The live clone pulls from the `release` branch (stable), not `main` (development line).
- **Role abstraction, no model names:** Portable files (`agent/`, `command/`, `skills/`,
  `templates/`, `scripts/`) contain NO concrete model/provider names. Model assignment lives
  exclusively in the local, gitignored `opencode.jsonc` of each machine.
- **Template constancy:** Constant sections of `templates/AGENTS.md` (workflow, git conventions,
  languages, prohibitions) are the binding interface — do not modify them in projects.
- **Phase-0 checkpoint is technically enforced:** `permission.task` gates architect → developer /
  qa-manager spawns (`"task": {"developer": "ask", "qa-manager": "ask"}` in the local JSON).

## Architecture: function vs connectivity

This repo's "product" is configuration and deterministic tooling, not a service:

- **`scripts/qa_compress.sh`** — deterministic log compression (checker-registry pattern).
- **`tests/`** — self-referential framework checks: pytest reads the repo's own portable files
  and asserts invariants (frontmatter intact, no model names, template exists, script syntax).
  These tests are the QA target for `qa_compress.sh` — no fakes needed beyond the file system.
- **`agent/`, `command/`, `skills/`, `templates/`** — data, not code: prompts and skeletons.
  Changes here need story + QA like everything else.

## Git conventions

- Every story = its own branch: `feature/<story-id>-<slug>`.
- **Worktree discipline:** Developer sessions work in their own Git worktree
  `.worktrees/<story-id>-<slug>/` (created by architect). Main working dir stays on `main`.
- **No direct push to `main`.** Merge only after QA gate (PASS).
- Commit body carries metadata for QA requeue:
  ```
  symbols: <changed export symbols> | breaks: <none|breaking> | affects: <dependent files> | tests: <pytest result>
  ```
- Planning docs (requirements, design, stories) are the architect's Phase 1+2 deliverable and are
  committed on `main` directly (no code, nothing testable yet — QA gating starts with stories).

## Workflow

0. **Planning checkpoint (mandatory before every dev/QA start)** — for every requirement
   (new feature, replanning, bugfix, "small" change):
   1. **Planning phase (architect):** requirements/design/stories, REQ-IDs, doc updates.
   2. **Review checkpoint (user):** architect presents the concrete implementation overview —
      WHAT (stories + developer targets), HOW (waves, order, test criteria). **Dev+QA never
      start without explicit user-go** ("passt"/"go").
   3. **Then:** dev + QA per approved plan.
   - Applies to small changes and bugfix loops too — no implicit starts.
1. **Stories:** `STORIES.md` (index) + `docs/stories/<phase>-<id>-<slug>.md`. Every story links
   traceability (`REQ-XXX` + design section) and contains **test criteria that exist BEFORE
   implementation**.
2. **Developer:** implements EXACTLY the developer targets — nothing more, nothing less.
   Tests first, `pytest` green.
3. **QA gate:** checks requirements, tests, role abstraction, template constancy.
   PASS → merge. FAIL → fix loop (max 3), then BLOCKED → back to architect/user.

## Languages

- Dialogue with user: respond in the user's language
- Code/identifiers: English
- Repo docs (README, requirements, design, stories): English
- Agent prompts: respond in the user's language

## Prohibitions

- No autonomous decomposition/implementation outside released stories.
- No unrequested features outside developer targets.
- No concrete model/provider names in portable files.
- No development in `~/.config/opencode` (live clone — pull only).
- No `git init`/writing outside the project path.

## References

- `docs/requirements.md` — source of truth for scope (REQ-IDs)
- `docs/design.md` — source of truth for architecture (two-clone, check design)
- `STORIES.md` — story index (status per story)
- `templates/AGENTS.md` — the skeleton every project fills in
- `netclip/AGENTS.md`, `intesis_modbus/CLAUDE.md` — reference projects