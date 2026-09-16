---
description: QA-Gate für Feature-Branch — prüft Requirements, Tests, Architektur-Trennung, Fake-Interfaces. Gibt PASS/FAIL/BLOCKED zurück. Auch Status-Dialog nach dem Plan.
agent: qa-manager
---

Prüfe QA-Gate / Status für: $ARGUMENTS

- WENN $ARGUMENTS leer und Implementierung läuft: agiere als Status-Dialogpartner — fasse zusammen: `STORIES.md` Status, alle `feature/*` Branches, letzte `pytest` Logs, offene FAILs/BLOCKEDs (Tabelle Story|Branch|Tests|QA|Fehler) und beantworte User-Frage zu Stand/Fehlern
- WENN $ARGUMENTS Branch `feature/<id>-<slug>` oder Story-ID: prüfe QA-Gate gegen `docs/requirements.md` + Story Akzeptanzkriterien, führe `pytest`/`ruff`/`mypy` aus, verifiziere Funktion vs Konnektivität + Fakes → PASS/FAIL/BLOCKED
- Spawn bei FAIL automatisch `developer` Fix auf gleichem Branch (Loop), bei BLOCKED eskaliere präzise Rückfrage an User
