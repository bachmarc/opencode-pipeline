---
id: F-007
title: Pipeline Enforcement Plugin
status: planned
owner: ""
---

## Vision

Pipeline process rules (merge discipline, dev-start gate, architect code guard, story status
tracking) are enforced deterministically via an opencode plugin — not just recommended in
prompts. The plugin intercepts tool calls (`tool.execute.before`) and blocks or redirects
violations before they happen. Behavioral prompt rules become hard technical gates.

## Context

The opencode-pipeline framework relies on prompt-based rules (AGENTS.md, agent/*.md) to enforce
process discipline: no merge without QA-PASS, no dev-start without user-go, architect writes no
code. But LLMs follow instructions probabilistically — they forget, skip, or creatively
reinterpret rules. The only hard gate today is `permission.task` (UI approval for subagent
spawns).

opencode's plugin system (`tool.execute.before`, `tool.execute.after`, events) provides the
mechanism to turn soft prompt rules into hard deterministic enforcement. This feature builds a
TypeScript plugin that lives in the repo's `plugins/` directory and deploys to
`~/.config/opencode/plugins/` via the existing release branch workflow.

### Guards

1. **Merge Guard** — `bash` tool calls containing `git merge` on main: plugin checks
   `.pipeline/qa-status/` for a PASS file matching the branch. No PASS → block.

2. **Dev-Start Guard** — `task` tool calls spawning `developer` or `qa-manager`: plugin
   verifies a story file exists and is in an appropriate state. Reinforces `permission.task`.

3. **Architect Code Guard** — `edit`/`write` tool calls targeting `src/`, `tests/`, `*.py`,
   `*.ts` (code files): plugin detects the current agent is architect and asks the user
   interactively: "Kleinigkeit (Housekeeping-Story) oder Pipeline starten?" If housekeeping,
   the change is logged in a default housekeeping story. If pipeline, the edit is blocked and
   the architect must create a proper story. Never silently allowed.

4. **Story Status Guard** — `bash` tool calls containing `git merge` on main: after successful
   merge, plugin checks whether STORIES.md was updated for the merged branch. If not → warning.

5. **Session Recovery Guard** — On the first tool call of a session (architect agent only):
   plugin runs `session_recovery.py --check`. If recovery items exist (open intents, dirty
   worktrees) → hard block until addressed. Prevents starting fresh work while previous
   session state is dangling. Fires once per session.

6. **Documenter Guard** — `bash` tool calls containing `git merge` on main: plugin checks
   the feature branch's commit history for a `docs: reconcile` commit (Documenter output).
   No documenter commit → block. Enforces the QA-PASS → Documenter → Merge sequence.

### Architecture

- **Plugin file:** `plugins/pipeline-enforcement.ts` — single entry point, multiple guards
  as composable functions.
- **Guard modules:** Each guard is a pure function: `(input, output) → void | throw Error`.
  Guards receive tool call context and either pass through, modify, or throw to block.
- **State access:** Guards read `.pipeline/` directory and `STORIES.md` for status checks.
  No external dependencies beyond the file system.
- **Agent detection:** Uses `context.agent` from the plugin context to identify which agent
  is making the call (architect vs developer vs qa-manager).
- **Deployment:** `plugins/` directory in repo → `release` branch → `git pull` in
  `~/.config/opencode` → opencode loads from `~/.config/opencode/plugins/`.

### What this feature does NOT include

- No changes to existing Python scripts (they remain as-is)
- No CI/CD integration (local enforcement only)
- No changes to the permission.task system (plugin complements it)
- No prompt-rule removal (prompts stay as behavioral training, plugin adds hard gates)

## Stories

- 11-01-plugin-scaffold (planned)
- 11-02-merge-guard (planned)
- 11-03-dev-start-guard (planned)
- 11-04-architect-code-guard (planned)
- 11-05-story-status-guard (planned)
- 11-06-prompt-integration (planned)
- 11-07-session-recovery-guard (planned)
- 11-08-documenter-guard (planned)
