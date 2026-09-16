---
description: Dekomponiere Requirements/Design in Features & Stories (STORIES.md + docs/stories/) — so geschnitten dass günstige Massenmodelle (lokal via agent.developer.model konfiguriert) sie per Branch implementieren können.
agent: architect
---

Dekomponiere basierend auf `docs/requirements.md` + `docs/design.md` für: $ARGUMENTS

- Erstelle `STORIES.md` (Phasen-Index wie vokabel) + `docs/stories/<phase>-<id>-<slug>.md` pro Story mit Definition, Developer Targets, Akzeptanz- und Testkriterien
- Stories so schneiden dass das lokal konfigurierte günstige Massenmodell (`agent.developer.model`) sie isoliert per feature/<id>-<slug> Branch implementieren kann
- Testkriterien müssen VOR Implementierung erfüllbar sein (Fakes!)

Wenn $ARGUMENTS leer: nutze aktuelles Projekt im cwd.
