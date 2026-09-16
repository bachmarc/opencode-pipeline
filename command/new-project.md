---
description: Lege neues Folder-Projekt mit Git + dev-workflow Struktur an (AGENTS.md, docs/, STORIES.md, tests/fakes, src/core + src/adapters). Ohne Argument initialisiert im aktuellen Folder (ersetzt /init).
agent: architect
---

Lege neues Projekt an: $ARGUMENTS

- WENN $ARGUMENTS leer (User ist schon im Ziel-Folder wie `Development/test`):
  - **WICHTIG:** Dein eigenes `cwd` ist NICHT das Ziel. Nutze als Projekt-Root GENAU diesen hier injizierten Sitzungs-Pfad:
    - Zielpfad = `!`pwd`` (dieser Befehl läuft im Root der User-Sitzung, nicht in deinem Subagenten-cwd)
  - Führe nur in diesem Zielpfad aus:
    - Prüfe dort `git status` — falls kein Repo: `git init && git checkout -b main`
    - Erstelle Grundstruktur dort falls fehlend: `AGENTS.md` (**aus Vorlage `~/.config/opencode/templates/AGENTS.md` kopieren + Platzhalter im Dialog ausfüllen — NICHT von Null improvisieren**), `docs/requirements.md`, `docs/design.md` (mit Fake-Pflicht), `STORIES.md`, `docs/stories/_template.md`, `tests/fakes/`, `src/core/`, `src/adapters/`, `.gitignore`, `README.md`, `opencode.json`
  - **Verbote:** Kein `mkdir`, kein `git init`, kein Schreiben außerhalb des injizierten Zielpfads. Niemals `git init` in deinem eigenen cwd oder im Workspace-Root.
  - Starte dann Requirements-Interview auf Deutsch (architect)
  - `/init` ist obsolet und muss nicht mehr benutzt werden
- WENN $ARGUMENTS Pfad/Name enthält (z.B. `mein-projekt` oder `/mnt/content_main/Development/neues-tool`):
  - Führe aus: `mkdir -p <pfad> && cd <pfad> && git init && git checkout -b main`
  - Erstelle dort gleiche Grundstruktur (AGENTS.md aus Vorlage `~/.config/opencode/templates/AGENTS.md`)
  - Starte dann Requirements-Interview

In beiden Fällen gilt: Folder + git ist Basis, danach folgt dev-workflow (Skill) Phase 1+2.
