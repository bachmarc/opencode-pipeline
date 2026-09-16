# STORIES.md — opencode-pipeline Dev Repo

**Phases:** Retro (traceability) → 01 Foundation → 02 Self-Checks → 03 Deploy
Index and status per story. Template: `docs/stories/_template.md`.

| Story | Titel | Status | Traceability |
|---|---|---|---|
| RETRO-01 | Model de-hardwiring (frontmatter) | Retro-Erledigt (e5c3ccb) | REQ-002 |
| RETRO-02 | Role abstraction (no model names in prompts) | Retro-Erledigt (0cef1c9) | REQ-002 |
| RETRO-03 | Phase-0 enforcement via permission.task | Retro-Erledigt (2ed3c6c) | REQ-002 |
| RETRO-04 | templates/AGENTS.md skeleton | Retro-Erledigt (1ecd1cf) | REQ-002 |
| RETRO-05 | README rework (EN + JSON procedure) | Retro-Erledigt (e7985ee, 2ed3c6c, 1ecd1cf) | REQ-002 |
| 01-01-foundation | Dev-repo AGENTS.md + docs + this index | Geplant | REQ-001, REQ-002 → Design §1, §2 |
| 01-02-retro-trace | Retro stories in STORIES.md + commits | Erledigt (mit 01-01 gemeinsam, Retro-Tabelle oben) | REQ-002 → Design §2 |
| 01-03-framework-checks | tests/test_framework.py (deterministic self-checks) | Erledigt (QA PASS, 71ce05c→544d703) | REQ-003, REQ-004 → Design §3 |
| 01-04-deploy-procedure | Deployment doc (pull + restart) in README | Erledigt (QA PASS, 3b301a4→d15257a) | REQ-005 → Design §4 |
| 01-05-version | APP_VERSION.py + bump rule | Erledigt (QA PASS, 0b144c1→e93e000) | Design §6 |

## Phasen-Kommentar

- **Retro:** Reine Nachdokumentation bereits direkt gemachter Änderungen — kein Re-Implementierungsauftrag.
- **Phase 01 (Foundation):** Repo-Hygiene, Docs, Index — Architect-Arbeit direkt auf `main`
  (keine testbaren Developer Targets).
- **Phase 02 (Self-Checks):** tests-first, Developer + QA-Gate.
- **Phase 03 (Deploy):** Doku; optional Command.