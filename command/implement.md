---
description: Implementiere eine Story isoliert per Git-Branch (feature/<id>-<slug>) mit billigem Modell — Tests zuerst, Fake-Interfaces, nur Developer Targets.
agent: developer
---

Implementiere Story: $ARGUMENTS

- Erwarte Story-ID wie `01-01`, `02-03` oder `feature/01-01-slug`
- Lege Branch `feature/<story-id>-<slug>` an (falls nicht existent)
- Implementiere exakt die Developer Targets aus `docs/stories/<id>.md`, Tests zuerst gemäß Testkriterien, nutze Fakes
- Prüfe `pytest` grün, dann Übergabe an qa-manager

Wenn $ARGUMENTS leer: liste offene Stories aus STORIES.md und frage welche.
