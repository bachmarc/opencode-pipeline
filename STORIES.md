# STORIES.md — opencode-pipeline Dev Repo

**Phases:** Retro (traceability) → 01 Foundation → 02 Self-Checks → 03 Deploy → 04 i18n → 05 Docs → 06 Pipeline Evolution → 11 Pipeline Enforcement → 12 Polyglot QA → 13 Project Migration → 14 Derived Docs → 15 Living Code Docs → 16 Clarification Markers → 17 Framework Path Consolidation → 18 Checker Evolution → 19 Python QA Toolchain → 20 Script Portability Fixes → 21 Documenter Scope Fix
Index and status per story. Template: `docs/features/_story_template.md`.

| Story | Title | Status | Traceability |
|---|---|---|---|
| RETRO-01 | Model de-hardwiring (frontmatter) | Retro-Done (e5c3ccb) | F-RETRO retro |
| RETRO-02 | Role abstraction (no model names in prompts) | Retro-Done (0cef1c9) | F-RETRO retro |
| RETRO-03 | Phase-0 enforcement via permission.task | Retro-Done (2ed3c6c) | F-RETRO retro |
| RETRO-04 | templates/AGENTS.md skeleton | Retro-Done (1ecd1cf) | F-RETRO retro |
| RETRO-05 | README rework (EN + JSON procedure) | Retro-Done (e7985ee, 2ed3c6c, 1ecd1cf) | F-RETRO retro |
| 01-01-foundation | Dev-repo AGENTS.md + docs + this index | Planned | F-001 foundation |
| 01-02-retro-trace | Retro stories in STORIES.md + commits | Done (with 01-01, retro table above) | F-001 foundation |
| 01-03-framework-checks | tests/test_framework.py (deterministic self-checks) | Done (QA PASS, 71ce05c→544d703) | F-001 foundation |
| 01-04-deploy-procedure | Deployment doc (pull + restart) in README | Done (QA PASS, 3b301a4→d15257a) | F-001 foundation |
| 01-05-version | APP_VERSION.py + bump rule | Done (QA PASS, 0b144c1→e93e000) | F-001 foundation |
| 04-01-translate-agents | Translate agent/*.md to English | Done (QA PASS, bb24add→b5cb8d5) | F-002 i18n |
| 04-02-translate-commands | Translate command/*.md to English | Done (QA PASS, 37883c3→49d31ef) | F-002 i18n |
| 04-03-translate-template | Translate templates/AGENTS.md to English | Done (QA PASS, 6f98276→f80825f) | F-002 i18n |
| 04-04-translate-repo-docs | Translate AGENTS.md + STORIES.md to English | Done (QA PASS, 50d2412→51c0919) | F-002 i18n |
| 05-01-readme-workflow-how | README: step-by-step workflow explanation (how, not just why) | Done (1706150) | F-003 docs |
| **06-01-feature-hierarchy** | **Feature→Story file structure + migration** | **Done (QA PASS, bf492fc)** | **F-004 pipeline-evolution** |
| **06-02-pipeline-dir-intent** | **.pipeline/ directory + intent tracking script** | **Done (QA PASS, 578be32)** | **F-004 pipeline-evolution** |
| **06-03-release-branch** | **Release branch setup + promote script** | **Done (QA PASS, 3ce3a89)** | **F-004 pipeline-evolution** |
| **06-04-worktree-setup** | **Deterministic worktree/branch setup script** | **Done (QA PASS, 1544279)** | **F-004 pipeline-evolution** |
| **06-05-pipeline-status** | **Pipeline status aggregation script** | **Done (QA PASS, 17cf54d)** | **F-004 pipeline-evolution** |
| **06-06-story-management** | **Story resolve/create/status-update scripts** | **Done (QA PASS, 80338ff)** | **F-004 pipeline-evolution** |
| **06-07-scaffold-project** | **Deterministic project scaffolding script** | **Done (QA PASS, 2e0586b)** | **F-004 pipeline-evolution** |
| **06-08-session-recovery** | **Session recovery script (full state scan)** | **Done (QA PASS, 762411d)** | **F-004 pipeline-evolution** |
| **06-09-feature-claim** | **Feature claim/release script (multi-user)** | **Done (QA PASS, b85e49c)** | **F-004 pipeline-evolution** |
| **06-10-documenter-agent** | **Documenter agent + /document command** | **Done (QA PASS, 97bd5f1)** | **F-004 pipeline-evolution** |
| **06-11-qa-scripts** | **QA routing, commit metadata, merge validation** | **Done (QA PASS, 18b3907)** | **F-004 pipeline-evolution** |
| **06-12-prompt-updates** | **Agent prompts: script integration + recovery** | **Done (QA PASS, 7108618)** | **F-004 pipeline-evolution** |
| **06-13-check-scripts** | **Template constancy + architecture check scripts** | **Done (QA PASS, 46e054a)** | **F-004 pipeline-evolution** |
| **06-14-orchestration-rules** | **Orchestration rules + QA self-enforcement** | **Done (QA PASS, 571287d)** | **F-004 pipeline-evolution** |
| **07-01-readme-restructure** | **README restructure (user-oriented documentation)** | **Done (QA PASS, 0bad86f)** | **F-003 docs** |
| **07-02-document-reasoning-effort** | **README + design.md: per-agent reasoning depth (`reasoningEffort`)** | **Done (QA PASS, 4e62287)** | **F-003 docs** |
| **07-03-free-edit-userdocs** | **End-user docs (`README.md` & co.) free-edit, no story/test criteria; prose README tests removed** | **Done (QA PASS, b11543d)** | **F-003 docs** |
| **08-01-templates-reform** | **Story + Feature templates with new sections** | **Done (QA PASS, 346bf12)** | **F-005 doc-model-reform** |
| **08-02-architect-prompt** | **Architect prompt: features/stories as primary source** | **Done (QA PASS, f901fa6)** | **F-005 doc-model-reform** |
| **08-03-documenter-prompt** | **Documenter prompt: generate summaries + consistency** | **Done (QA PASS, a56dc8b)** | **F-005 doc-model-reform** |
| **09-01-migrate-features** | **Migrate feature.md files to new format** | **Done (QA PASS, 5aeea63)** | **F-006 doc-model-migration** |
| **09-02-migrate-stories** | **Migrate story files to new 5-section format** | **Done (QA PASS, e25b424)** | **F-006 doc-model-migration** |
| **09-03-migrate-indexes** | **Migrate STORIES.md + FEATURES.md to feature-references** | **Done (QA PASS, cf5b3f3)** | **F-006 doc-model-migration** |
| **09-04-migrate-summaries** | **Rewrite requirements.md + design.md as summaries** | **Done (QA PASS, f61671f)** | **F-006 doc-model-migration** |
| **09-05-migrate-prompts-commands** | **Update QA/dev prompts + commands + AGENTS.md template** | **Done (QA PASS, 2394a20)** | **F-006 doc-model-migration** |
| **09-06-migrate-scripts-tests** | **Update scripts + tests for new model** | **Done (QA PASS, 4e285f2)** | **F-006 doc-model-migration** |
| **10-01-remove-legacy-stories-dir** | **Remove legacy `docs/stories/` directory** | **Done (QA PASS, 5230bd1)** | **F-004 pipeline-evolution** |
| 11-01-plugin-scaffold | Plugin scaffold and infrastructure | **Done (QA PASS, 6f17eed)** | F-007 pipeline-enforcement |
| 11-02-merge-guard | Merge guard (block without QA-PASS) | **Done (QA PASS, 603ea75)** | F-007 pipeline-enforcement |
| 11-03-dev-start-guard | Dev-start guard (warn without story) | **Done (QA PASS, 8121d3c)** | F-007 pipeline-enforcement |
| 11-04-architect-code-guard | Architect code guard (interactive housekeeping) | **Done (QA PASS, 466c2cd)** | F-007 pipeline-enforcement |
| 11-05-story-status-guard | Story status guard (warn after merge) | **Done (QA PASS, c133636)** | F-007 pipeline-enforcement |
| 11-06-prompt-integration | Prompt integration and documentation | **Done (QA PASS, 466be79)** | F-007 pipeline-enforcement |
| 11-07-session-recovery-guard | Session recovery guard (block on session start) | **Done (QA PASS, d725ca3)** | F-007 pipeline-enforcement |
| 11-08-documenter-guard | Documenter guard (block merge without documenter) | **Done (QA PASS, 3055169)** | F-007 pipeline-enforcement |
| 12-01-qa-config-contract | QA config contract + config-driven checker dispatch | Done (QA PASS, 93591cf→afc8fcb) | F-008 polyglot-qa |
| 12-02-checker-rspec-jest | Checker plugins: rspec (Ruby) + jest (JavaScript) | Done (QA PASS, cbc1d55→f578433) | F-008 polyglot-qa |
| 12-03-checker-gradle-maven | Checker plugins: gradle + maven (Java) | Done (QA PASS, 9a08022→5f0f279) | F-008 polyglot-qa |
| 12-04-checker-json-yaml | Checker plugins: JSON + YAML syntax validation | Done (QA PASS, e316058→5dac5b0) | F-008 polyglot-qa |
| 12-05-checker-html | Checker plugin: HTML (simple syntax check) | Done (QA PASS, 374ad8f→9da3597) | F-008 polyglot-qa |
| 12-06-commit-metadata-polyglot | Polyglot commit metadata (test command from config, language-aware symbols) | Done (QA PASS, 4886916→2b3649e) | F-008 polyglot-qa |
| 12-07-prompt-genericization | Genericize portable prompts: no runner names | Done (QA PASS, 3804ec3→88dfa53) | F-008 polyglot-qa |
| 12-08-template-scaffold-config | Template config sections + scaffold + own qa_config.json | Done (QA PASS, d1d0f33→93c8648) | F-008 polyglot-qa |
| 12-09-template-migration-tool | Template migration tool for existing projects | Done (QA PASS, d8273b8→d06e2bd) | F-008 polyglot-qa |
| 12-10-check-architecture-polyglot | check_architecture.py: polyglot import checking (JS/Ruby/Java) | Done (QA PASS, e28fac5→813549d) | F-008 polyglot-qa |
| 12-11-test-suite-green | Fix pre-existing test failures blocking QA gate | Done (QA PASS, 8308e6d→5f1a8bb) | F-008 polyglot-qa |
| 12-12-dev-start-guard-slug | Dev-start-guard: strip story slug when parsing STORIES.md | Done (QA PASS, 45049b2→f020a99) | F-008 polyglot-qa |
| 13-01-migrate-command | /migrate-project command + migrate-project skill scaffold | Done (172537a) | F-009 project-migration |
| 13-02-project-analyzer | Project analysis script (stack detection, structure scan) | Done (172537a) | F-009 project-migration |
| 13-03-agents-md-generator | AGENTS.md draft generation (template + project extraction) | Done (172537a) | F-009 project-migration |
| 13-04-structure-provisioning | Missing directory/file provisioning | Done (172537a) | F-009 project-migration |
| 13-05-retro-story-generator | Optional retro story creation for pre-pipeline work | Done (172537a) | F-009 project-migration |
| 13-06-migration-validation | Post-migration validation (structure + template constancy) | Done (172537a) | F-009 project-migration |
| 14-01-remove-derived-docs | Remove requirements.md + design.md from entire framework | Done (QA PASS, 7a000ae→1468340) | F-010 eliminate-derived-docs |
| 15-00-numbered-feature-folders | Rename feature folders to F-<ID>-<slug> convention | Done (QA PASS, aef58d6→389e9c3) | F-011 living-code-docs |
| 15-01-code-doc-rule | Code documentation rule in story template + developer prompt | Done (QA PASS, f3f4675→069d941) | F-011 living-code-docs |
| 15-02-watermark-readme | Watermark in README.md and AGENTS.md + check script | Done (QA PASS, 1b16589→9e0ad89) | F-011 living-code-docs |
| 15-03-documenter-incremental | Documenter incremental update mode (watermark-based) | Done (QA PASS, 6c1f7f2→28b0c85) | F-011 living-code-docs |
| 15-04-dev-start-guard-marker | Dev-start guard: explicit [story: XX-YY] marker | Done (QA PASS, ed98c4e→2d570ff) | F-011 living-code-docs |
| 16-01-clarification-markers | Clarification markers in story template + workflow | Done (QA PASS, 5c3b1e0→79b6ad9) | F-012 clarification-markers |
| 17-01-plugin-relative-paths | Guards resolve scripts via import.meta.dirname, fail-closed | Done (QA PASS, e486ea7→619a068) | F-013 framework-path-consolidation |
| 17-02-verdict-schema-fix | merge-guard.ts reads verdicts[] not last_verdict | Done (QA PASS, 1d29d19→41c6bb3) | F-013 framework-path-consolidation |
| 17-03-enforcement-bypass-fix | merge_if_passed.py carries guard logic itself | Done (QA PASS, eef4e62→3b462e9) | F-013 framework-path-consolidation |
| 17-04-qa-compress-sole-entry | Prompts forbid direct pytest, qa_compress.sh only | Done (QA PASS, 963c04e→1088ae8) | F-013 framework-path-consolidation |
| 17-05-prompt-script-refs | Prompts drop scripts/ paths, describe actions only | Done (QA PASS, dd50c98→0650436) | F-013 framework-path-consolidation |
| 18-01-check-architecture-file-mode | check_architecture.py: explicit file-list mode (root-layout projects) | Planned | F-014 architecture-checker-evolution |
| 19-01-qa-compress-python | qa_compress.py: Python QA entry point (replaces bash) | Done (QA PASS, d74bc5a→5f5c581) | F-019 python-qa-toolchain |
| 19-02-session-recovery-pull | session_recovery.py: git pull at startup + test_resolve_by_id fix | Done (QA PASS, 5381e1d→627485d) | F-019 python-qa-toolchain |
| 20-01-resolve-story-root | resolve_story.py + story_status.py: get_repo_root() via CWD Git-traversal | Done (QA PASS, 4c300ec) | F-020 script-portability-fixes |
| 20-02-worktree-unc-paths | worktree_setup.py: git -C pattern for UNC-path compatibility | Done (QA PASS, ff297c8) | F-020 script-portability-fixes |
| 20-03-qa-compress-py-mandatory | developer.md + qa-manager.md: qa_compress.py as mandatory sole test entry point | Done (QA PASS, a61380a) | F-020 script-portability-fixes |
| 21-01-documenter-scope-fix | merge_if_passed.py + documenter-guard.ts: branch-exclusive git log scope | Planned | F-021 documenter-scope-fix |
| 21-02-documenter-catchup | Documenter catch-up run for Stories 15-00..20-03 | Planned | F-021 documenter-scope-fix |

- **Retro:** Pure retroactive documentation of changes already made directly — no re-implementation.
- **Phase 01 (Foundation):** Repo hygiene, docs, index — architect work directly on `main`
  (no testable developer targets).
- **Phase 02 (Self-Checks):** Tests-first, developer + QA gate.
- **Phase 03 (Deploy):** Documentation; optional command.
- **Phase 04 (i18n):** Translate all portable files from German to English (F-002 i18n).
- **Phase 05 (Docs):** User-facing documentation improvements (README workflow explanation).
- **Phase 06 (Pipeline Evolution):** Feature hierarchy, deterministic scripts, session
  resilience, multi-user claim, documenter agent, agent prompt updates. 13 stories in 5
  implementation waves:
  - Wave 1 (06-01..03): Foundation — file hierarchy, .pipeline dir, release branch
  - Wave 2 (06-04..07): Core scripts — worktree, status, story mgmt, scaffolding
  - Wave 3 (06-08..09): Recovery + claim — session recovery, feature claim
  - Wave 4 (06-10): Documenter agent
  - Wave 5 (06-11..13): QA scripts, agent prompt updates, check scripts
- **Phase 07 (Docs Restructure):** README restructure for end-user documentation.
  User-oriented flow: pitch → process → install → reference.
- **Phase 08 (Doc Model Reform):** Shift documentation model from architect-primary
  to feature/story-primary. Templates, architect prompt, documenter prompt.
  - Wave 1 (08-01, 08-02): Templates + Architect prompt (parallel)
  - Wave 2 (08-03): Documenter prompt (depends on new model being defined)
- **Phase 09 (Doc Model Migration):** Migrate existing repo data to new model.
  6 stories in 3 waves:
  - Wave 1 (09-01, 09-02): Features + Stories files (parallel, data only)
  - Wave 2 (09-03, 09-04): Indexes + Summaries (parallel, depend on migrated data)
  - Wave 3 (09-05, 09-06): Prompts/Commands + Scripts/Tests (parallel, depend on summaries)
- **Phase 11 (Pipeline Enforcement):** TypeScript opencode plugin for deterministic process
  enforcement. 7 stories in 3 waves:
  - Wave 1 (11-01): Plugin scaffold — infrastructure, guard registry
  - Wave 2 (11-02, 11-03, 11-04, 11-05, 11-07, 11-08): All 6 guards parallel — isolated modules
  - Wave 3 (11-06): Prompt integration — documentation updates
- **Phase 12 (Polyglot QA Gate):** Runner abstraction for the QA gate — any language
  (Ruby, JavaScript, Java, JSON/YAML config repos, HTML), mixed projects via checker
  list in `qa_config.json`. 10 stories in 4 waves:
  - Wave 1 (12-01): Config contract + config-driven dispatch in qa_compress.sh
  - Wave 2 (12-02, 12-03, 12-04, 12-05): Checker plugins parallel — rspec/jest,
    gradle/maven, json/yaml, html (one file each, no shared-file edits)
  - Wave 3 (12-06, 12-07, 12-08, 12-09): Commit metadata polyglot, prompt
    genericization, template + scaffold + own config, migration tool
  - Wave 4 (12-10): check_architecture.py polyglot — automated core-purity
    check for JS/Ruby/Java (parallel with Wave 3, independent of it)
- **Phase 13 (Project Migration):** Interactive migration of existing projects into the
  pipeline framework. Command + Skill + 4 deterministic scripts + validation. 6 stories in 3 waves:
  - Wave 1 (13-01, 13-02): Command/Skill scaffold + Project analyzer (parallel)
  - Wave 2 (13-03, 13-04, 13-05): AGENTS.md generator + Structure provisioning + Retro stories (parallel)
  - Wave 3 (13-06): Migration validation (depends on all prior scripts)
- **Phase 14 (Eliminate Derived Docs):** Remove `docs/requirements.md` and `docs/design.md`
  from the entire framework. Single source of truth: features + stories + AGENTS.md.
  Architect quick-start via `session_recovery.py` + `FEATURES.md`. 1 story:
  - 14-01: Remove all references, tests, scaffold targets, delete files
- **Phase 15 (Living Code Documentation):** Code-level docs as source of truth,
  watermark-based incremental updates for README.md and AGENTS.md. Inspired by
  OpenSpec's living specs concept, adapted to avoid the drift that killed
  docs/design.md. 4 stories in 3 waves:
  - Wave 1 (15-00): Numbered feature folders (rename all existing folders)
  - Wave 2 (15-01): Code-doc rule in templates + prompts (foundation)
   - Wave 3 (15-02, 15-03): Watermark infrastructure + Documenter update (parallel)
- **Phase 16 (Clarification Markers):** `[NEEDS CLARIFICATION]` markers as first-class
  concept in story templates + architect/QA prompts. Template-level change, no scripts.
  Inspired by spec-kit's clarify pattern. 1 story:
  - 16-01: Marker guidance in story template, architect prompt, QA prompt
- **Phase 17 (Framework Path Consolidation):** Fix the dogfood blind spot — framework scripts
  were assumed project-local but only exist in the framework installation. Guards resolve
  scripts via `import.meta.dirname` (plugin-relative, platform-independent). Fail-closed
  session recovery. Verdict schema unified. Enforcement bypass closed. qa_compress.sh as
  sole test entry point. Prompts drop script paths. 5 stories in 3 waves:
  - Wave 1 (17-01, 17-02): Plugin-relative paths + Verdict schema fix (parallel)
  - Wave 2 (17-03, 17-04): Enforcement bypass fix + qa_compress.sh sole entry (parallel)
  - Wave 3 (17-05): Prompts drop script paths (after 17-04 to avoid conflicts)
- **Phase 18 (Architecture Checker Evolution):** check_architecture.py file-list mode —
  first-class support for root-layout projects (core/adapter separation in root files
  instead of src/core/). Surfaced during intesis_modbus onboarding (F-009 case):
  directory-only invocation cannot express "check these core files" without also
  checking the adapter. 1 story (candidate, not scheduled):
  - 18-01: `--files` mode, byte-identical directory mode, shared per-file check unit
- **Phase 19 (Python QA Toolchain):** Replace `qa_compress.sh` and all `qa_checkers/*.sh`
  with Python equivalents — the framework is already all-Python except for these bash files.
  Fixes 26 test failures on Windows (`/bin/bash` not found). Also integrates `git pull`
  into `session_recovery.py` and fixes a fragile status assertion in `test_resolve_by_id`.
  2 stories, parallel:
  - 19-01: `qa_compress.py` + 8 Python checker modules, bash files deleted
  - 19-02: `git pull` in `session_recovery.py` + `test_resolve_by_id` status assertion removed
- **Phase 20 (Script Portability Fixes):** Two portability bugs reported on Windows UNC paths.
  `resolve_story.py` + `story_status.py` use `Path(__file__).parent.parent` for repo root
  (resolves to framework dir, not project dir) — fix: `get_repo_root()` with Git-traversal
  from `Path.cwd()`. `worktree_setup.py` passes UNC paths as `cwd=` to subprocess (WinError 267)
  — fix: `git -C <path>` instead of `cwd=<path>` for worktree-local commands. 2 stories, parallel:
  - 20-01: `get_repo_root()` in `resolve_story.py` + `story_status.py`
  - 20-02: `git -C` pattern in `worktree_setup.py` for UNC-path compatibility
  - 20-03: `qa_compress.py` as mandatory sole entry point in `developer.md` + `qa-manager.md`
- **Phase 21 (Documenter Scope Fix):** `git log <branch>` traversed full ancestry, so old
  Phase-12 `docs: reconcile` commits on `main` satisfied the check for every branch — the
  Documenter was never actually enforced since Phase 13. Fix: scope to `main..<branch>` in
  both `merge_if_passed.py` and `documenter-guard.ts`. Follow-up: one-time catch-up Documenter
  run for all stories 15-00..20-03. 2 stories:
  - 21-01: Branch-exclusive scope fix in merge_if_passed.py + documenter-guard.ts + tests
  - 21-02: Documenter catch-up run on main (Documenter agent, not developer)
