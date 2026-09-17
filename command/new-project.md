---
description: Create new folder project with Git + dev-workflow structure (AGENTS.md, docs/, STORIES.md, tests/fakes, src/core + src/adapters). Without argument initializes in current folder (replaces /init).
agent: architect
---

Create new project: $ARGUMENTS

- IF $ARGUMENTS empty (user is already in target folder like `Development/test`):
  - **IMPORTANT:** Your own `cwd` is NOT the target. Use as project root EXACTLY this injected session path:
    - Target path = `!`pwd`` (this command runs in the root of the user session, not in your subagent cwd)
  - Execute only in this target path:
    - Check `git status` there — if no repo: `git init && git checkout -b main`
    - Create base structure there if missing: `AGENTS.md` (**copy from template `~/.config/opencode/templates/AGENTS.md` + fill placeholders in dialogue — do NOT improvise from scratch**), `docs/requirements.md`, `docs/design.md` (with fake requirement), `STORIES.md`, `docs/stories/_template.md`, `tests/fakes/`, `src/core/`, `src/adapters/`, `.gitignore`, `README.md`, `opencode.json`
  - **Prohibitions:** No `mkdir`, no `git init`, no writing outside the injected target path. Never `git init` in your own cwd or in workspace root.
  - Then start requirements interview in German (architect)
  - `/init` is obsolete and no longer needs to be used
- IF $ARGUMENTS contains path/name (e.g. `my-project` or `/mnt/content_main/Development/new-tool`):
  - Execute: `mkdir -p <path> && cd <path> && git init && git checkout -b main`
  - Create same base structure there (AGENTS.md from template `~/.config/opencode/templates/AGENTS.md`)
  - Then start requirements interview

In both cases: folder + git is base, then dev-workflow (skill) phase 1+2 follows.
