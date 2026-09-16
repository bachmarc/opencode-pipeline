---
description: Zeigt Implementierungs-Stand aller Stories und Fehler — Dialog mit QA-Manager nach dem Plan.
agent: qa-manager
---

Zeige Status für: $ARGUMENTS

- Aggregiere `STORIES.md`, `git branch -a`, letzte Commits, `pytest`/`ruff` Ergebnisse, offene QA-FAILs/BLOCKEDs
- Antworte auf Deutsch kompakt (Tabelle), dann Details zu: $ARGUMENTS
- Wenn $ARGUMENTS leer: Gesamt-Status aller Stories. Wenn Story-ID/Branch genannt: Detail-Status + Fehler für diese Story.
