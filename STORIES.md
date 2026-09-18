# STORIES.md — opencode-pipeline Dev Repo

**Phases:** Retro (traceability) → 01 Foundation → 02 Self-Checks → 03 Deploy → 04 i18n → 05 Docs → 06 Pipeline Evolution
Index and status per story. Template: `docs/stories/_template.md`.

| Story | Title | Status | Traceability |
|---|---|---|---|
| RETRO-01 | Model de-hardwiring (frontmatter) | Retro-Done (e5c3ccb) | REQ-002 |
| RETRO-02 | Role abstraction (no model names in prompts) | Retro-Done (0cef1c9) | REQ-002 |
| RETRO-03 | Phase-0 enforcement via permission.task | Retro-Done (2ed3c6c) | REQ-002 |
| RETRO-04 | templates/AGENTS.md skeleton | Retro-Done (1ecd1cf) | REQ-002 |
| RETRO-05 | README rework (EN + JSON procedure) | Retro-Done (e7985ee, 2ed3c6c, 1ecd1cf) | REQ-002 |
| 01-01-foundation | Dev-repo AGENTS.md + docs + this index | Planned | REQ-001, REQ-002 → Design §1, §2 |
| 01-02-retro-trace | Retro stories in STORIES.md + commits | Done (with 01-01, retro table above) | REQ-002 → Design §2 |
| 01-03-framework-checks | tests/test_framework.py (deterministic self-checks) | Done (QA PASS, 71ce05c→544d703) | REQ-003, REQ-004 → Design §3 |
| 01-04-deploy-procedure | Deployment doc (pull + restart) in README | Done (QA PASS, 3b301a4→d15257a) | REQ-005 → Design §4 |
| 01-05-version | APP_VERSION.py + bump rule | Done (QA PASS, 0b144c1→e93e000) | Design §6 |
| 04-01-translate-agents | Translate agent/*.md to English | Done (QA PASS, bb24add→b5cb8d5) | REQ-007, NFR-001 → Design §8 |
| 04-02-translate-commands | Translate command/*.md to English | Done (QA PASS, 37883c3→49d31ef) | REQ-007, NFR-001 → Design §8 |
| 04-03-translate-template | Translate templates/AGENTS.md to English | Done (QA PASS, 6f98276→f80825f) | REQ-007, NFR-001 → Design §8 |
| 04-04-translate-repo-docs | Translate AGENTS.md + STORIES.md to English | Done (QA PASS, 50d2412→51c0919) | REQ-007, NFR-001 → Design §8 |
| 05-01-readme-workflow-how | README: step-by-step workflow explanation (how, not just why) | Done (1706150) | REQ-008 → Design §4 |
| **06-01-feature-hierarchy** | **Feature→Story file structure + migration** | **Done (QA PASS, bf492fc)** | **REQ-009 → Design §9** |
| **06-02-pipeline-dir-intent** | **.pipeline/ directory + intent tracking script** | **Done (QA PASS, 578be32)** | **REQ-011 → Design §11** |
| **06-03-release-branch** | **Release branch setup + promote script** | **Done (QA PASS, 3ce3a89)** | **REQ-001a → Design §1** |
| **06-04-worktree-setup** | **Deterministic worktree/branch setup script** | **Done (QA PASS, 1544279)** | **REQ-013.1 → Design §13** |
| **06-05-pipeline-status** | **Pipeline status aggregation script** | **Done (QA PASS, 17cf54d)** | **REQ-013.2 → Design §13** |
| **06-06-story-management** | **Story resolve/create/status-update scripts** | **Done (QA PASS, 80338ff)** | **REQ-013.6,7,10 → Design §13** |
| **06-07-scaffold-project** | **Deterministic project scaffolding script** | **Done (QA PASS, 2e0586b)** | **REQ-013.3 → Design §13** |
| **06-08-session-recovery** | **Session recovery script (full state scan)** | **Done (QA PASS, 762411d)** | **REQ-011 → Design §11** |
| **06-09-feature-claim** | **Feature claim/release script (multi-user)** | **Done (QA PASS, b85e49c)** | **REQ-010 → Design §10** |
| **06-10-documenter-agent** | **Documenter agent + /document command** | **Done (QA PASS, 97bd5f1)** | **REQ-012 → Design §12** |
| **06-11-qa-scripts** | **QA routing, commit metadata, merge validation** | **Done (QA PASS, 18b3907)** | **REQ-013.5,8,9 → Design §13** |
| **06-12-prompt-updates** | **Agent prompts: script integration + recovery** | **Done (QA PASS, 7108618)** | **REQ-013, NFR-004 → Design §13** |
| **06-13-check-scripts** | **Template constancy + architecture check scripts** | **Done (QA PASS, 46e054a)** | **REQ-013.4,11 → Design §13** |
| **06-14-orchestration-rules** | **Orchestration rules + QA self-enforcement** | **Done (QA PASS, 571287d)** | **NFR-004 → Design §13** |
| **07-01-readme-restructure** | **README restructure (user-oriented documentation)** | **Planned** | **REQ-014 → Design §15** |
| **08-01-templates-reform** | **Story + Feature templates with new sections** | **Done (QA PASS, 346bf12)** | **F-005 doc-model-reform** |
| **08-02-architect-prompt** | **Architect prompt: features/stories as primary source** | **Done (QA PASS, f901fa6)** | **F-005 doc-model-reform** |
| **08-03-documenter-prompt** | **Documenter prompt: generate summaries + consistency** | **Done (QA PASS, a56dc8b)** | **F-005 doc-model-reform** |
| **09-01-migrate-features** | **Migrate feature.md files to new format** | **Planned** | **F-006 doc-model-migration** |
| **09-02-migrate-stories** | **Migrate story files to new 5-section format** | **Planned** | **F-006 doc-model-migration** |
| **09-03-migrate-indexes** | **Migrate STORIES.md + FEATURES.md to feature-references** | **Planned** | **F-006 doc-model-migration** |
| **09-04-migrate-summaries** | **Rewrite requirements.md + design.md as summaries** | **Planned** | **F-006 doc-model-migration** |
| **09-05-migrate-prompts-commands** | **Update QA/dev prompts + commands + AGENTS.md template** | **Planned** | **F-006 doc-model-migration** |
| **09-06-migrate-scripts-tests** | **Update scripts + tests for new model** | **Planned** | **F-006 doc-model-migration** |

## Phase comments

- **Retro:** Pure retroactive documentation of changes already made directly — no re-implementation.
- **Phase 01 (Foundation):** Repo hygiene, docs, index — architect work directly on `main`
  (no testable developer targets).
- **Phase 02 (Self-Checks):** Tests-first, developer + QA gate.
- **Phase 03 (Deploy):** Documentation; optional command.
- **Phase 04 (i18n):** Translate all portable files from German to English (REQ-007).
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