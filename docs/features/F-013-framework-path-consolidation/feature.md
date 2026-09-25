---
id: F-013
title: Framework Path Consolidation
status: planned
owner: ""
req: []
---

## Vision

The pipeline framework works correctly in any project — not just the dogfood repo. Framework
scripts are resolved from the framework installation (`~/.config/opencode/scripts/`) via
plugin-relative paths, never assumed to be present in the project directory. Guards are
fail-closed. The enforcement system has no bypass gaps. All configured checkers run on every
QA cycle.

## Context

The framework was developed dogfooded: scripts lived both in `~/.config/opencode/scripts/`
and in the dev repo's own `scripts/` directory. Prompts and guards referenced `scripts/…`
as project-relative paths — which worked in the dogfood repo but silently failed in any
other project (intesis_modbus, netclip, vokabel).

Four additional latent bugs were discovered during the first real cross-project session:

1. **Script path resolution** — Guards check `${directory}/scripts/session_recovery.py`
   (project-relative). Missing → silent skip (fail-open). Should resolve via plugin-relative
   `import.meta.dirname` → `../scripts/` (framework installation, platform-independent).

2. **Verdict schema mismatch** — `merge-guard.ts` reads `status.last_verdict` (key never
   written). `qa_route.py` writes `{"verdicts": [...]}`. Direct `git merge` would be blocked
   even with a valid QA-PASS.

3. **Enforcement bypass** — `merge_if_passed.py` calls `git merge` via Python subprocess.
   Guards only intercept literal shell `git merge` commands → the recommended merge path
   bypasses its own guard. `merge_if_passed.py` must carry the guard logic itself.

4. **qa_compress.sh not the sole entry point** — `developer.md` and `qa-manager.md` allow
   direct `pytest` calls. `qa_config.json` checkers (e.g. `yaml`) are silently skipped.
   `qa_compress.sh` must be the only test entry point in all prompts.

**Target audience:** Any developer using the pipeline on a project other than opencode-pipeline
itself.

**Scope boundaries (what does NOT belong):**
- Changing how scripts work internally (only path resolution changes)
- Adding new scripts or checkers
- Changing project-level files (AGENTS.md, qa_config.json) in existing projects
- CI/CD or deployment changes

## Architecture

**Plugin-relative path resolution (platform-independent):**

```typescript
import { join } from "path"
// import.meta.dirname = directory of the plugin file
// Plugin lives in: ~/.config/opencode/plugins/
// Scripts live in: ~/.config/opencode/scripts/
const FRAMEWORK_SCRIPTS = join(import.meta.dirname, "..", "scripts")
const scriptPath = join(FRAMEWORK_SCRIPTS, "session_recovery.py")
```

This works on Windows (`C:\Users\…\.config\opencode\scripts\`) and Unix
(`/home/…/.config/opencode/scripts/`) without any environment variable or hardcoded path.

**Fail-closed session recovery:**
If `scriptPath` does not exist → throw `"Framework not installed: scripts/session_recovery.py
not found at <path>. Reinstall opencode-pipeline."` — never silent skip.

**Verdict schema (single source of truth):**
`qa_route.py` writes `{"verdicts": [{"verdict": "PASS"|"FAIL", …}]}`.
All readers use `data["verdicts"][-1]["verdict"]`. Key `last_verdict` is removed from
`merge-guard.ts`.

**Enforcement in merge_if_passed.py:**
Script reads `.pipeline/qa-state/<id>.json`, checks `verdicts[-1].verdict == "PASS"`,
checks for `docs: reconcile` commit on branch — before calling `git merge`. Plugin guard
remains as second layer for direct `git merge` shell commands.

**qa_compress.sh as sole entry point:**
Prompts say "run the test suite" without a path. `qa_compress.sh` is described as the
framework's test runner. Direct `pytest` is only mentioned as a checker name in
`qa_config.json` context, never as a command to run directly.

## Stories

- 01-01-plugin-relative-paths (planned)
- 17-01-plugin-relative-paths (planned) — Guards resolve scripts via import.meta.dirname, fail-closed
- 17-02-verdict-schema-fix (planned) — merge-guard.ts reads verdicts[] not last_verdict
- 17-03-enforcement-bypass-fix (planned) — merge_if_passed.py carries guard logic itself
- 17-04-qa-compress-sole-entry (planned) — Prompts forbid direct pytest, qa_compress.sh only
- 17-05-prompt-script-refs (planned) — Prompts drop script paths, describe actions only
