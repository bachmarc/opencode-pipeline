# Design — opencode-pipeline Dev Repo

**Status:** Derived summary generated from features and stories · **Purpose:** Architecture overview and design decisions

This document is a **derived summary** generated from the feature and story hierarchy. It provides a high-level overview of architectural patterns, design decisions, and key infrastructure. For detailed context and implementation guidance, refer to the individual feature and story files in `docs/features/`.

## Architecture Overview

### Two-Clone Topology

**Reference:** F-001 Foundation

```
github.com:bachmarc/opencode-pipeline.git
        │
        ├── main branch                              development line
        │     - features merge here after QA-PASS
        │     - may be unstable between milestones
        │
        ├── release branch                           stable / deployable
        │     - promoted from main (conscious step)
        │     - always a known-good state
        │
        ├── ~/Development/opencode-pipeline          DEV clone
        │     - full pipeline workflow: stories, branches, worktrees, QA gate
        │     - pytest self-checks run here
        │     - tracks main (and feature branches)
        │
        └── ~/.config/opencode                       LIVE clone
              - read-only: git pull release + opencode restart
              - gitignored local state stays untouched: opencode.jsonc, cron.db
```

Deployment is manual and staged: after promoting `main` → `release`, the user pulls `release` in the live clone and restarts opencode. The live clone's working tree must never be edited. The promotion `main` → `release` is a fast-forward merge or reset, only done when the user considers `main` stable enough for production use.

### Self-Check Architecture

**Reference:** F-001 Foundation

This repo's "product" is configuration; its invariants are checkable by reading itself:

- **`tests/test_framework.py`** — pytest, stdlib only. Checks:
  1. `agent/*.md` frontmatter: parseable YAML block, no `model:` key (models live in the local `opencode.jsonc` only), required keys present (`description`, `mode`)
  2. No concrete model/provider names in portable files (`agent/`, `command/`, `skills/`, `templates/`, `scripts/`): regex over known patterns (e.g. `glm-`, `deepseek`, `qwen`, `haiku`, `claude-`, `ollama-docker`, `:cloud`), with an explicit allowlist for legitimate references (e.g. `CLAUDE.md` filename mentions)
  3. `templates/AGENTS.md` exists and contains the constant section markers (Workflow, Git conventions, Languages, Prohibitions) plus `<...>` placeholders
  4. `scripts/qa_compress.sh` passes `bash -n` (syntax) and has the exec bit

- **Fake perspective:** The only "external dependency" is the file system — pytest tmp_path and the repo files themselves. No fakes needed; checks are pure and deterministic.
- **QA integration:** `pytest tests/` output is compressed by `qa_compress.sh` as usual — the QA gate now has a deterministic target for this repo.

### Deploy Procedure

**Reference:** F-001 Foundation

Documented in README (§ Deployment): `git pull` in `~/.config/opencode` + restart of opencode (config is loaded once at startup). Optional convenience later; manual is the default. The local `opencode.jsonc`/`cron.db` are gitignored and survive pulls untouched.

### Template Constancy

**Reference:** F-001 Foundation

`templates/AGENTS.md` sections Workflow / Git conventions / Languages / Prohibitions are the binding interface. The self-check (§ Self-Check Architecture, check 3) asserts their presence so accidental deletion or restructuring fails QA.

### Versioning

**Reference:** F-001 Foundation

`APP_VERSION = "0.1.0"` in `APP_VERSION.py` at repo root; bump on notable merges (documented in STORIES.md). Traceability anchor for releases.

### English-First Portable Files

**Reference:** F-002 Internationalization (English)

All portable files (`agent/`, `command/`, `templates/`, `scripts/`) are written in English: prose, section headers, frontmatter descriptions, inline comments.

**Dialogue language is decoupled from prompt language.** The `templates/AGENTS.md` section "Languages" configures the user-facing dialogue language per project. The framework default is: "Respond in the user's language." This allows English prompts to drive German, English, or any other dialogue — the prompt instructs the agent *what* to do, the Languages section tells it *which language* to use with the user.

### Feature → Story Hierarchy

**Reference:** F-004 Pipeline Evolution

#### File-system layout

```
docs/
  features/
    <feature-name>/
      feature.md          # scope, status, traceability (REQ-ID), claim info
      stories/
        <phase>-<id>-<slug>.md   # individual story (same format as today)
FEATURES.md               # top-level index: feature | status | owner | stories
```

**`feature.md` fields:**

```yaml
---
id: F-001
title: Session Resilience
status: planned | claimed | in-progress | qa-pending | done
owner: ""                    # user@host when claimed
req: []                       # empty in new model
---
## Vision
...
## Context
...
## Stories
- 06-01-intent-tracking (planned)
- 06-02-recovery-script (planned)
```

**`FEATURES.md`** is a flat index (like today's `STORIES.md`) for quick overview:

```
| Feature | Title | Status | Owner | Stories | Traceability |
|---------|-------|--------|-------|---------|--------------|
| F-001   | ...   | planned | —    | 06-01, 06-02 | — |
```

**Status derivation:** A feature's status is the minimum of its stories' statuses (all done → feature done; any in-progress → feature in-progress; any planned → not done).

#### Machine access pattern

Agents resolve state by:
1. Read `FEATURES.md` for overview (O(1) file read)
2. Read `docs/features/<name>/feature.md` for detail (O(1))
3. Read `docs/features/<name>/stories/<id>.md` for story specifics (O(1))

No parsing of large aggregated files; each level is a single predictable path.

### Multi-User Feature Isolation

**Reference:** F-004 Pipeline Evolution

#### Claim lifecycle

```
planned ──claim──► claimed (user@host, timestamp)
                       │
                       ├──work──► in-progress
                       │              │
                       │              ├──qa-pass──► done
                       │              └──release──► planned (stale/abort)
                       │
                       └──release──► planned
```

#### `scripts/feature_claim.py`

```
feature_claim.py claim <feature-name>     # pull → check → write status → commit → push
feature_claim.py release <feature-name>   # reset status → commit → push
feature_claim.py status                   # list all features with claim state (JSON)
feature_claim.py check-stale [--hours 24] # find claims older than threshold
```

**Atomicity:** The script does `git pull --rebase` before writing, then `commit + push`. If push fails (concurrent edit), it retries (pull + re-check + push, max 3 attempts). If the feature is already claimed by someone else, exit code 1 + error JSON.

**Branch signal:** `feature_claim.py claim` also creates the `feature/<name>` branch if it doesn't exist. The branch's existence on the remote is a secondary claim signal visible in GitHub.

#### Agent integration

- Architect calls `feature_claim.py status` to see what's available
- Developer calls `feature_claim.py claim <name>` before starting work
- On merge or abort: `feature_claim.py release <name>`
- Agents never edit `feature.md` status fields directly

### Session Resilience / Recovery

**Reference:** F-004 Pipeline Evolution

#### Intent tracking

`.pipeline/intent.json`:
```json
{
  "story_id": "06-01",
  "feature": "session-resilience",
  "agent": "developer",
  "step": "implement tests for intent tracking",
  "worktree": ".worktrees/06-01-intent-tracking",
  "branch": "feature/06-01-intent-tracking",
  "started_at": "2026-09-18T10:30:00Z",
  "done": false
}
```

**Write discipline:** The responsible agent writes the intent BEFORE starting the action. On completion, sets `"done": true`. History is appended (JSON-lines or array) so the full trail is visible.

#### `scripts/session_recovery.py`

Runs at session start (triggered by agent prompt instruction). Collects:

```json
{
  "open_intents": [...],
  "worktrees": [
    {
      "path": ".worktrees/06-01-intent-tracking",
      "branch": "feature/06-01-intent-tracking",
      "uncommitted_files": ["tests/test_intent.py"],
      "staged_files": [],
      "merge_conflicts": false,
      "detached_head": false
    }
  ],
  "main_state": {
    "ahead": 0, "behind": 2, "dirty": false
  },
  "qa_state": {
    "06-01": {"last_verdict": "FAIL", "fail_count": 1, "design_fix_count": 0}
  },
  "feature_claims": [
    {"feature": "session-resilience", "owner": "user@host", "since": "..."}
  ]
}
```

The agent prompt for architect/developer/qa-manager includes an instruction:
> "At session start, run `scripts/session_recovery.py`. If open intents or dirty worktrees exist, present the recovery summary to the user BEFORE doing anything else."

#### Worktree recovery

The recovery script specifically handles the scenario described in the requirements discussion: developer subagents created worktrees with half-finished changes, then the session died. The script:
1. Lists all `.worktrees/` entries
2. For each: checks `git status`, `git log --oneline -3`, staged/unstaged changes
3. Reports whether the worktree's branch was pushed to remote
4. The agent can then offer: continue work, stash + park, or discard

### Documenter Agent

**Reference:** F-004 Pipeline Evolution

#### Role definition

```yaml
# agent/documenter.md (frontmatter)
---
description: "Documentation consistency agent on cheap model. Reconciles docs, README,
  docstrings, and comments against actual code state. Runs after QA-PASS (before merge)
  and on manual /document command."
mode: subagent
temperature: 0.2
---
```

#### Trigger integration

**Automatic (after QA-PASS):**
The QA-Manager prompt includes: "On PASS verdict, before signaling merge-ready to Architect, spawn `documenter` with the feature branch diff as context."

**Manual:**
`command/document.md` — user invokes `/document [feature-name|story-id]`.

#### Documenter workflow

1. Receive git diff (from QA-Manager or `/document` command)
2. Read affected source files + current `docs/` state
3. Check and update:
   - README sections that reference changed functionality
   - `docs/design.md` sections affected by the change
   - Docstrings / method headers in changed files
   - Remove stale comments that reference old behavior
   - Feature/story docs: ensure status fields are current
4. Commit documentation changes on the same branch
5. Report what was updated (compact summary)

#### Boundary: what the Documenter does NOT do

- Does not make architecture decisions (that's the Architect)
- Does not write new code (that's the Developer)
- Does not judge correctness (that's QA)
- Does not invent documentation for unchanged code
- Relies on Architect/Developer/QA having done their work — synthesizes, doesn't create

### Deterministic Pipeline Scripts

**Reference:** F-004 Pipeline Evolution

#### Design principle

```
┌─────────────┐     calls      ┌──────────────────┐     reads/writes     ┌──────────┐
│  LLM Agent  │ ──────────────►│  scripts/*.py     │ ───────────────────► │ Git / FS │
│  (reasoning,│     exit code  │  (deterministic,  │                      │          │
│   dialogue) │ ◄──────────────│   atomic, tested) │ ◄─────────────────── │          │
└─────────────┘     + JSON     └──────────────────┘      file state       └──────────┘
```

**Agents call scripts via shell.** Scripts output JSON to stdout (machine-readable) and human-readable summaries to stderr. Exit code 0 = success, non-zero = specific error. Agents parse stdout JSON; they never grep/sed/awk the repo state themselves.

#### Script inventory

| Script | Feature | Input | Output | Called by |
|--------|---------|-------|--------|----------|
| `worktree_setup.py` | F-004 | story-id | worktree path (JSON) | Architect |
| `pipeline_status.py` | F-004 | — | full state JSON | QA-Manager, Architect |
| `scaffold_project.py` | F-004 | target-path | created files list | Architect |
| `feature_claim.py` | F-004 | claim/release/status | claim state JSON | All agents |
| `session_recovery.py` | F-004 | — | recovery state JSON | All agents (session start) |
| `prepare_commit_metadata.py` | F-004 | — (reads git diff) | commit msg template | Developer |
| `resolve_story.py` | F-004 | story-id or branch | story metadata JSON | All agents |
| `story_status.py` | F-004 | story-id, new-status | updated file path | Architect, QA |
| `qa_route.py` | F-004 | story-id, verdict | next agent + context JSON | QA-Manager |
| `merge_if_passed.py` | F-004 | branch | merge result | Architect |
| `create_story.py` | F-004 | phase, slug, req-id | story file path | Architect |
| `check_template_constancy.py` | F-004 | project AGENTS.md path | diff/PASS/FAIL | QA-Manager |

#### `.pipeline/` directory

All mutable pipeline state lives under `.pipeline/` (gitignored for local-only state, or tracked for shared state):

```
.pipeline/
  intent.json          # current/last intent (F-004) — tracked in git
  qa-state/            # per-story QA verdict history — tracked in git
    <story-id>.json
  config.json          # pipeline config overrides (optional) — gitignored
```

**Tracked vs. gitignored:** `intent.json` and `qa-state/` are committed so other sessions (multi-user) can see the pipeline state. `config.json` is local.

#### Testing

All scripts are tested in `tests/` with pytest. Tests use the repo's own files or `tmp_path` fixtures. Scripts are pure (no network calls except git push/pull, which is mocked in tests). This extends the existing self-check pattern (F-001 Foundation).

### Orchestration Principles

**Reference:** F-004 Pipeline Evolution

#### Phase 3 token optimization

The architect's role in Phase 3 (implementation) is decision-making and dialogue, not mechanical orchestration. All deterministic work (worktree setup, status queries, merge decisions) is delegated to scripts. This minimizes architect token usage on the expensive model and allows cheap models to handle the repetitive parts (developer, QA-Manager).

**Pytest discipline:** Pytest runs exactly **twice** per story — once by the Developer (before commit, to verify their own work) and once by the QA-Manager (independent verification). The Architect never runs pytest: not before QA, not after merge. Exception: merge conflicts that required manual resolution — then one verification run.

**Principle:** Architect calls scripts for state queries and atomic operations; scripts return JSON; architect interprets and decides. No free-hand LLM orchestration.

#### Pipeline streaming

QA does not wait for all developers to finish before starting. Each story's QA runs independently as soon as its developer reports completion. This enables parallel development and QA, reducing total pipeline latency.

**Principle:** Start QA per story, not per wave. No batch-QA (multiple stories in one QA invocation).

#### QA self-enforcement

The QA-Manager enforces a single-story rule: if a prompt contains multiple stories, QA checks only the first and returns FAIL with reason "Batch-QA forbidden — invoke separately per story." This prevents context degradation on cheap models and ensures deterministic, focused evaluation.

**Principle:** One story per QA invocation. Cheap models work best with focused scope.

#### Determinism boundary

Operations requiring atomicity, state consistency, or format determinism (concurrency, merge conflicts, file state) must use scripts, not LLM free-hand. The architect proactively recommends script-based solutions and does not accept LLM-only approaches for operations that need determinism.

**Principle:** If it needs to be atomic or deterministic, use a script. LLM handles reasoning and dialogue; scripts handle state.

### Documentation Model

**Reference:** F-005 Documentation Model Reform

Features become more than folders — they carry their own vision and context that describes what all their stories together create. Stories become self-contained: they carry their own purpose, requirements, and acceptance criteria without needing to reference external REQ-IDs.

The Documenter's role expands: after implementation, it generates/updates `requirements.md` and `design.md` as derived summaries with feature/story references, serving as a quick-start for the Architect in the next session.

### README Structure

**Reference:** F-003 Documentation

The README targets **opencode users who are new to multi-agent setups**. Structure follows a user-oriented flow (pitch → process → install → reference), not an inside-out dump of internals.

**Free-edit area:** `README.md` and user-facing docs are **free-edit** — any agent (build, architect, developer) can edit them directly without creating a story or test criteria. Internal/derived docs (`docs/requirements.md`, `docs/design.md`, feature/story infrastructure) remain governed by the Documenter workflow and test suite.

#### Section layout

```
1. Intro / Pitch (ausführlich, ~1-2 screens)
   - What the framework does for developers (elevator pitch)
   - The four roles: Architect thinks, Developer writes, QA checks, Documenter reconciles
   - Repo contents woven into prose (agent/, scripts/, templates/, command/, ...)
   - Key design principles (cheap models for mass, deterministic scripts, config-as-code)
   - Note: no opencode.jsonc in repo (local, gitignored)

2. Development Process (the heart)
   - Mermaid flowchart (prominent)
   - Phase 1: Design dialogue (User ↔ Architect)
   - Phase 2: User-Go checkpoint
   - Phase 3: Autonomous Dev+QA (worktrees, qa_compress, JSON verdicts)
   - Escalation paths (FAIL → fix loop, BLOCKED_Design → Architect, BLOCKED_Requirements → User)
   - Command quick-reference table

3. Installation
   - 3a: Fresh install (git clone → ~/.config/opencode)
   - 3b: Existing setup (git init + remote add + fetch + checkout in existing dir)
   - Local opencode.jsonc creation (example)
   - Forward-links to Technical Details for model assignment, Phase-0 enforcement

4. Technical Details (reference sections, linked from above)
   - How model assignment works (role vs. machine separation, per-agent reasoning depth via `reasoningEffort`)
   - Phase-0 checkpoint enforcement (permission.task)
   - The four agents in detail (table)
   - Deployment (branching strategy, promotion, rollback, live clone)
   - Extending qa_compress.sh (checker-registry pattern, plugin files in `scripts/qa_checkers/` — checkers: pytest (default), rspec, jest; see stories 12-01-qa-config-contract, 12-02-checker-rspec-jest)
   - Per-project AGENTS.md (template, constancy)
   - Architecture pattern (function vs. connectivity)

5. Open points / outlook (brief)
```

## Decisions

| # | Decision | Reason | Feature |
|---|---|---|---|
| D1 | No CI yet | local pytest + QA gate is the contract; CI later | F-001 |
| D2 | Live clone pulls `release`, not `main` | `main` is dev line (may be unstable); `release` = conscious stable promotion | F-001 |
| D3 | All portable files English | international team; dialogue language per project | F-002 |
| D4 | Self-checks read the repo only | zero infra, deterministic, cheap-model-evaluable | F-001 |
| D5 | Scripts over LLM free-hand | Anything requiring atomicity, state, format consistency, or concurrency → deterministic script; LLM calls script + interprets result | F-004 |
| D6 | Feature = work unit per user/session | Stories are implementation slices; features are the planning/claiming/merging unit | F-004 |
| D7 | Claim = script + branch + status file | No LLM-managed concurrency; `feature_claim.py` handles atomic claim/release | F-004 |
| D8 | Intent file for session recovery | `.pipeline/intent.json` is the single re-entry point after crash/disconnect | F-004 |
| D9 | Documenter on cheap model | Documentation consistency is repetitive reconciliation, not creative reasoning | F-004 |
| D10 | Repo contents in prose, not isolated table | Reads naturally in the pitch; table was disconnected from context | F-003 |
| D11 | Two installation paths (fresh + existing) | Users with existing opencode.jsonc must not lose their config | F-003 |
| D12 | Technical details as anchored sections at end of README | All in one file (user preference), but not cluttering the intro flow | F-003 |
| D13 | Forward-links from Installation to Details | Installation stays short; curious users can drill down | F-003 |
| D14 | Checkers as self-registering plugins, declared per project | New runner = one file + registration line, no shared-file edits; project declares stack in `qa_config.json` | F-008 |
