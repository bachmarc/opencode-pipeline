# Story 07-01 — README restructure (user-oriented documentation)

Status: Done
Feature: docs (F-003)

## Context / Purpose

The README is currently structured inside-out (folder table → design decisions →
installation → deployment → workflow). It needs to be restructured into a user-oriented
flow targeting opencode users who are new to multi-agent setups. Content is also
editorially revised — not just reordered.

## Requirements

After this story, the README follows the structure: Intro/Pitch → Development Process →
Installation (fresh + existing setup) → Technical Details (reference) → Open Points.
The content is tightened, improved, and adapted to the target audience. Technical details
that were previously scattered are consolidated at the end and linked from earlier sections.

## Developer Targets (exactly, no more / no less)

- **`README.md`** — complete rewrite with the following section structure:

  1. **Intro / Pitch** (~1-2 screens, ausführlich):
     - Opening: what the framework does for developers (multi-agent pipeline as config-as-code)
     - The four roles introduced: Architect thinks, Developer writes, QA checks, Documenter reconciles
     - Repo contents woven into prose (not an isolated table): `agent/`, `scripts/`, `templates/`, `command/`, `docs/features/`, `.pipeline/`
     - Key design principles as bullet points: cheap models for mass work, deterministic scripts over LLM free-hand, config-as-code (clone & go), tests before code
     - Note about `opencode.jsonc` being local/gitignored
     - Note about per-agent model assignment (configured locally, not in role files)

  2. **Development Process** (the heart of the README):
     - Mermaid flowchart (prominent, same content as current)
     - Phase 1: Design dialogue (User ↔ Architect) — what happens, what comes out
     - Phase 2: User-Go checkpoint — why it exists, how it works (prompt + permission.task)
     - Phase 3: Autonomous Dev+QA — Developer in worktrees, QA with qa_compress, JSON verdicts, parallel execution
     - Escalation paths: FAIL → fix loop (max 3), BLOCKED_Design → Architect (autonomous), BLOCKED_Requirements → User
     - Command quick-reference table (same commands as current)

  3. **Installation**:
     - **3a Fresh install**: `git clone` to `~/.config/opencode` (release branch)
     - **3b Existing setup**: `git init` + `git remote add` + `git fetch` + `git checkout -b release --track origin/release` in existing `~/.config/opencode` — preserves local files (`opencode.jsonc`, `cron.db`)
     - Local `opencode.jsonc` creation with example JSON
     - Restart opencode → done
     - Forward-links to Technical Details for model assignment and Phase-0 enforcement

  4. **Technical Details** (reference sections with anchor IDs, linked from above):
     - How model assignment works (role vs. machine separation, the JSON procedure)
     - Phase-0 checkpoint enforcement (permission.task system)
     - The four agents in detail (table: role, model tier, mode, output, budget)
     - Deployment (two-clone topology, branching strategy main/release, promotion script, rollback, live clone pull)
     - Extending qa_compress.sh (checker-registry pattern, example)
     - Per-project AGENTS.md (template usage, constancy rule)
     - Architecture pattern projects must follow (function vs. connectivity: src/core/ zero-imports, src/adapters/ thin wrappers, mandatory fakes)

  5. **Open points / outlook** (brief, same content as current)

- **No other files changed.** Only `README.md` is modified.

## Acceptance criteria (checked by qa-manager)

- README.md exists and is valid Markdown
- Section order is: Intro/Pitch → Development Process → Installation → Technical Details → Open Points
- Intro section mentions all four agent roles and weaves repo folder contents into prose (no isolated folder table)
- Development Process contains a Mermaid flowchart and covers Phase 1, 2, 3 + escalation paths
- Installation has two clearly separated paths: fresh install (git clone) and existing setup (git init + remote add + pull)
- Existing-setup instructions include `git init`, `git remote add`, `git fetch`, `git checkout -b release --track origin/release`
- Technical Details sections have anchor IDs and are linked from Installation section
- All commands from the current quick-reference table are present
- No content from the current README is lost (may be reworded/restructured, but all topics covered)
- Language is English throughout
- No concrete model/provider names in the README (only placeholders like `provider/strong`, `provider/cheap`)

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_readme_structure.py::test_readme_section_order` — Reads README.md, asserts the five top-level sections appear in order (by heading text or anchor)
- `tests/test_readme_structure.py::test_readme_has_mermaid_flowchart` — Asserts README contains a ```mermaid code block
- `tests/test_readme_structure.py::test_readme_installation_two_paths` — Asserts README contains both "Fresh install" / "fresh" and "Existing setup" / "existing" subsections under Installation
- `tests/test_readme_structure.py::test_readme_existing_setup_git_init` — Asserts the existing-setup section contains `git init`, `git remote add`, `git fetch`, `git checkout`
- `tests/test_readme_structure.py::test_readme_no_model_names` — Reuses the existing model-name regex from test_framework.py to scan README for concrete model/provider names
- `tests/test_readme_structure.py::test_readme_agent_roles_in_intro` — Asserts the intro section mentions all four roles: architect, developer, qa-manager, documenter
- `tests/test_readme_structure.py::test_readme_technical_details_anchors` — Asserts Technical Details sections have anchor IDs and at least one forward-link from Installation references them
