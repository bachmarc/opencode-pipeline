---
id: F-027
title: Tooling-Gate Bootstrap
status: planned
owner: ""
req: []
---

## Vision

Every project onboarded through the pipeline — whether via `/migrate` or `/new-project` —
arrives with a **fully working, self-contained test pipeline** that covers not just tests
but also lint, typecheck, format-check, and security audit. No global tool dependencies.
No silent gaps. QA cannot PASS a story unless all configured tooling gates are green.

The framework enforces this at three levels:
1. **Story Template** — every story has a mandatory Tooling Gates section; QA checks it.
2. **Checkers** — `qa_compress.py` knows how to run lint/typecheck/format/audit for all
   standard stacks (JS/TS, Python, Ruby, Java, JSON/YAML).
3. **Onboarding** — `analyze_project.py` detects which tooling gates are missing and
   `provision_structure.py` writes a complete `qa_config.json` with all relevant checkers.
   For unknown stacks, the Architect researches and creates a bootstrap story.

## Context

**Root cause (VirtOffice incident):** Story 01-01 passed QA despite broken tooling:
`npm run lint` failed (wrong flag), `npm run typecheck` and `npm run format:check` didn't
exist, ESLint 8 was incompatible with Node 24, TypeScript 7 was hoisted instead of 5.x.
None of this was caught because:
- The story template had no Tooling Gates section → Developer didn't write them
- QA only checks what's in the story → QA didn't check them
- `qa_compress.py` has no eslint/tsc/prettier checkers → couldn't have checked even if asked
- `analyze_project.py` detects test checkers but not lint/typecheck/format checkers
- `provision_structure.py` writes `{"checkers": ["jest"]}` — silent about the rest

**Design decisions:**

- **Separate checker names per tool:** `eslint`, `tsc`, `prettier`, `npm-audit`, `mypy`,
  `ruff`, `black`, `rubocop`, `checkstyle` — one name per tool in `qa_config.json`.
  Granular: a project can opt out of one gate without losing others.
  
- **All relevant checkers auto-detected at onboarding:** `analyze_project.py` writes
  complete `qa_config.json` for each stack:
  - JS/TS: `["jest", "eslint", "tsc", "prettier", "npm-audit"]`
  - Python: `["pytest", "mypy", "ruff"]`
  - Ruby: `["rspec", "rubocop"]`
  - Java: `["gradle"/"maven", "checkstyle"]`
  - JSON/YAML: `["json", "yaml"]` (already exist)
  - Unknown: Architect researches, creates bootstrap story

- **Tool not found = exit 1:** If a configured checker can't find its binary
  (e.g. `eslint` not installed), the checker outputs a clear error and exits 1.
  Developer must fix via story or manual install — no silent skip, no auto-install.

- **Local-only, no globals:** All checkers invoke tools via project-local paths first
  (`node_modules/.bin/eslint`, `npx eslint`) before falling back to PATH. This enforces
  the "no global dependency" contract.

- **Story Template enforcement:** The `_story_template.md` gets a mandatory
  `## Tooling Gates` section. QA-Manager's checklist explicitly covers it.
  Architect prompt gets a runtime-version question for scaffold stories.

- **Architect runtime interview:** For any scaffold story (new project, 01-xx),
  Architect must ask: runtime version (Node 24? Python 3.11?), package manager
  (npm/yarn/pnpm?), existing tooling constraints. These go into the story as
  "Environment Constraints". Version mismatches (ESLint 8 + Node 24) become
  explicit story targets, not silent failures.

## Stories

- 27-01 story-template-tooling-gates (planned) — template + architect prompt + QA prompt
- 27-02 js-ts-lint-checkers (planned) — eslint, tsc, prettier, npm-audit checkers
- 27-03 python-lint-checkers (planned) — mypy, ruff, black checkers
- 27-04 ruby-java-lint-checkers (planned) — rubocop, checkstyle checkers
- 27-05 qa-gap-detection (planned) — analyze_project.py + provision_structure.py complete qa_config.json
