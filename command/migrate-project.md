---
description: Migrate an existing project into the opencode pipeline framework
agent: architect
---

Migrate existing project: $ARGUMENTS

- IF $ARGUMENTS empty (user is already in target folder):
   - **IMPORTANT:** Your own `cwd` is NOT the target. Use as project root EXACTLY this injected session path:
     - Target path = `!`pwd`` (this command runs in the root of the user session, not in your subagent cwd)
   - Execute only in this target path:
     - Check `git status` there — if no repo: `git init && git checkout -b main`
     - Verify this is an existing project (has source code, existing git history, or existing AGENTS.md)
   - Then load the `migrate-project` skill to guide the migration workflow
- IF $ARGUMENTS contains path/name (e.g. `../existing-project` or `/path/to/project`):
   - Verify the path exists and contains an existing project
   - Then load the `migrate-project` skill to guide the migration workflow

**Load the migrate-project skill** to proceed with the 6-phase migration workflow:
- Phase 1: Analyze the project structure
- Phase 2: Present analysis and confirm stack/branch
- Phase 3: Generate AGENTS.md interactively
- Phase 4: Provision missing structure
- Phase 5: Optional retro stories
- Phase 6: Validate migration

The skill will guide you through each phase step by step.
