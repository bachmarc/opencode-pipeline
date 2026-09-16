# AGENTS.md — <Projektname>

> Vorlage aus der opencode-Pipeline (`templates/AGENTS.md`). Ausfüllen: alles in `<...>`.
> Konstante Abschnitte (Workflow, Git, Sprachen, Verbote) **nicht** projekt-spezifisch abändern —
> sie sind die verbindliche Schnittstelle zwischen Framework und Projekt.
> Projekt-spezifisch: Projektname, Stack, Kernregeln, Referenzen (§ „Dieses Projekt").

## Dieses Projekt: <Name, One-Liner>

- **Was:** <1-2 Sätze: Problem, Zielgruppe, Abgrenzung — aus `docs/requirements.md`>
- **Stack:** <z.B. Python 3.12, FastAPI + uvicorn, statisches HTML/JS-Frontend, Docker>
- **Versionierung:** `APP_VERSION = "0.1.0"` (in `src/<version>.py` o.ä.) — bei jedem Merge bumpen

## Kernregeln (Projekt-Source-of-Truth: `docs/requirements.md` + `docs/design.md`)

- <Kernregel 1 — z.B. "`src/core/board.py` (`PostBoard`) kennt kein FastAPI, kein HTTP, keine Uhr. Zeit kommt als Parameter (`now`).">
- <Kernregel 2 — z.B. "RAM-only: Keine Persistenz, keine Auto-Clear-Timer.">
- <… weitere, aus `docs/design.md` § Kern-Entscheidungen übernommen>
- **Fake-Pflicht:** Für JEDE externe Abhängigkeit (`<API>`, `<DB>`, `<HA>`, …) existiert ein Fake in `tests/fakes/` — Tests laufen ohne echte Systeme.

## Architektur: Funktion vs Konnektivität

Strikte Trennung (Muster: `intesis_modbus/CLAUDE.md`):

- **`src/core/`** — reine Logik/Algorithmen.
  - **Null Imports** aus Framework/IO/HA/DB/API.
  - Bekommt alle Daten als Parameter, gibt Dicts/Primitives zurück.
  - Vollständig unit-testbar, enthält Simulation-Helper (`simuliere_<x>()`).
- **`src/adapters/`** — dünne Wrapper (3-10 Zeilen pro Methode).
  - Extrahiert Request-Daten, **delegiert alle Entscheidungen an Core**, gibt HTTP-Antwort / schreibt Bus.
  - Timer/Listener/Scheduler ausschließlich hier.
- **Fakes sind Pflicht** für jede externe Abhängigkeit: `tests/fakes/`.
  - Core-Tests laufen **ohne** echte Systeme (`FakeClock`, `Fake<X>`-Interfaces).
  - **Fake = gleiche Methoden-Signaturen wie der echte Adapter.** Fakes die ein anderes
    Interface bieten als der Adapter → Designfehler. Der echte Orchestrierungs-Code muss
    mit Fakes aufrufbar sein, ohne Anpassungen.
  - Ist Core nicht ohne Fakes testbar → Designfehler.
- **Integration-Tests testen den echten Orchestrierungs-Code** (z.B. `Scheduler._run_cycle()`
  mit Fakes), nicht einen manuellen Nachbau des Zyklus. Manuell nachgebaute Zyklen umgehen
  Wiring-Bugs und sind wertlos als Integrationsnachweis.

## Git-Konvention

- Jede Story = eigener Branch: `feature/<story-id>-<slug>` (z.B. `feature/01-02-<slug>`).
- **Worktree-Pflicht:** Jede Developer-Session arbeitet in einem eigenen Git-Worktree
  `.worktrees/<story-id>-<slug>/` (angelegt vom architect). Das Hauptverzeichnis bleibt
  **immer auf `main`** (Merges, Hygiene). Zwei Agenten teilen NIE ein Working Directory.
- **Kein direkter Push auf `main`.** Merge nur nach QA-Gate (PASS).
- **Merge-Sperre ohne QA:** Architect darf `git merge` auf `main`/`master` **ausschließlich**
  ausführen wenn der QA-Manager für genau diesen Branch ein explizites `PASS` zurückgegeben
  hat. Kein Merge bei „Tests sind grün" allein — QA prüft mehr als pytest (Architektur,
  Targets, Commit-Metadaten). Wurde QA übersprungen, ist der Merge ungültig.
- Commit-Body enthält Metadaten für QA-Requeue:
  ```
  symbols: <geänderte Export-Symbols> | breaks: <none|breaking> | affects: <abhängige Files> | tests: <pytest-Ergebnis>
  ```

## Workflow

0. **Planungs-Checkpoint (PFLICHT vor jedem Dev/QA-Start)** — Reihenfolge für jede
   Anforderung/Änderung (auch Replannings!):
   1. **Planungsphase (architect):** Requirements/Design/Stories entwerfen, Doku anpassen
      (REQ-IDs, Design-Abschnitte, Story-Dateien).
   2. **Review-Checkpoint (User):** architect stellt dem User die konkrete Umsetzungs-
      übersicht vor — WAS wird implementiert (Stories + Developer Targets), WIE läuft es ab
      (Wellen, Reihenfolge, Fakes, Testkriterien). **Dev+QA starten NICHT ohne explizites
      User-Go** („passt"/„go"). Rückmeldungen fließen zurück in die Planung (Schleife).
   3. **Erst dann:** Dev + QA gemäß freigegebenem Plan.
   - Gilt auch für „kleine" Änderungen und Bugfix-Loops — kein implizites Starten.
1. **Stories**: `STORIES.md` (Index) + `docs/stories/<phase>-<id>-<slug>.md`.
   Jede Story verlinkt Traceability (`REQ-XXX` + Design-Abschnitt) und enthält
   **Testkriterien, die VOR Implementierung existieren (Fake-basiert)**.
2. **Developer**: implementiert GENAU die Developer Targets — nichts mehr, nichts weniger.
   Tests zuerst schreiben, `pytest` muss grün sein.
3. **QA-Gate (PFLICHT vor jedem Merge)**: Architect spawnt `qa-manager` für jeden
   Feature-Branch **bevor** er mergt. QA prüft: Requirements, Tests, Architektur-Trennung,
   Fake-Nutzung, Commit-Metadaten. Ergebnis:
   - PASS → Architect darf mergen.
   - FAIL → Developer-Fix-Loop (max. 3), dann BLOCKED → zurück an architect/User.
   - BLOCKED_Design → Architect korrigiert Design autonom (max. 2 Fixes).
   - BLOCKED_Requirements → Eskalation an User.
   **Kein Branch wird ohne QA-PASS gemergt. Keine Ausnahme.**

## Sprachen

- Dialog mit User: Deutsch
- Code/Bezeichner: Englisch
- UI-Texte: Deutsch

## Verbote

- **Architect schreibt keinen Code.** Alles unter `src/`, `tests/`, `utils/`, `main.py`,
  `models/` — jede Datei die Anwendungs-/Testcode enthält — wird ausschließlich vom
  `developer`-Agent auf einem Feature-Branch bearbeitet. Auch Einzeiler-Bugfixes.
  Auch „offensichtliche" Fixes. Keine Ausnahme.
- Kein autonomes Dekomponieren/Implementieren außerhalb freigegebener Stories.
- Keine unangefragten Features außerhalb der Developer Targets.
- Keine Imports von IO/Framework in `src/core/`.
- Kein `git init`/Schreiben außerhalb des Projekt-Pfads.
- **Subagent-Pfad-Disziplin:** Alle Befehle ausschließlich im zugeteilten Worktree;
  kein `/tmp`, kein `pip install`, keine Pfade außerhalb des Projekt-Roots.

## Referenzen

- `docs/requirements.md` — Source of Truth für Umfang (REQ-IDs)
- `docs/design.md` — Source of Truth für Architektur (Fakes, Kern-Regeln)
- `STORIES.md` — Story-Index (Status pro Story)
- <Projekt-spezifisch: `intesis_modbus/CLAUDE.md`, `vokabel/STORIES.md`, …>