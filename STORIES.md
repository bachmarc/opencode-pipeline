# STORIES.md — opencode-pipeline Dev Repo

**Phases:** Retro (traceability) → 01 Foundation → 02 Self-Checks → 03 Deploy → 04 i18n → 05 Docs
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
| 05-01-readme-workflow-how | README: step-by-step workflow explanation (how, not just why) | Planned | REQ-008 → Design §4 |

## Phase comments

- **Retro:** Pure retroactive documentation of changes already made directly — no re-implementation.
- **Phase 01 (Foundation):** Repo hygiene, docs, index — architect work directly on `main`
  (no testable developer targets).
- **Phase 02 (Self-Checks):** Tests-first, developer + QA gate.
- **Phase 03 (Deploy):** Documentation; optional command.
- **Phase 04 (i18n):** Translate all portable files from German to English (REQ-007).
- **Phase 05 (Docs):** User-facing documentation improvements (README workflow explanation).