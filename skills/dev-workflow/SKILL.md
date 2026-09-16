---
name: dev-workflow
description: >
  Use when starting or running a new software project in a folder with git.
  Triggers on "neues projekt", "requirements", "design besprechen", "features", "stories", "testbar", "fake schnittstellen", "qa prüfen", "branch".
  Implements Requirements → Design (with Fake Interfaces) → Stories → Tests-first → Cheap Dev per Git Branch → QA-Gate → Feedback Loop.
  Based on intesis_modbus architecture (Funktion vs Konnektivität) and vokabel story workflow.
---

# Dev Workflow — Folder-Projekte mit Git, Fake-Interfaces & QA-Gate

Dieser Skill standardisiert deinen wiederkehrenden Workflow für Folder-basierte Software-Projekte.

## Wann aktivieren

- User will ein neues Projekt anlegen ("neues projekt", "projekt anlegen", "folder")
- Requirements sammeln / Design besprechen
- Features/Stories erstellen lassen
- Testbarkeit ohne externe Systeme (Fakes)
- QA-Gate / Review

## Workflow-Phasen (strikte Reihenfolge)

### Phase 0 — Planungs-Checkpoint (PFLICHT vor jedem Dev/QA-Start)

Gilt für JEDEN Anforderungstyp: Neues Projekt, Replanning nach User-Feedback,
Bugfixes, "kleine" Änderungen. Reihenfolge:

1. **Planungsphase (architect):** Requirements/Design/Stories entwerfen, Doku anpassen
   (REQ-IDs, Design-Abschnitte, Story-Dateien — alles im Dialog, wie Phasen 1+2).
2. **Review-Checkpoint (User):** architect stellt dem User die konkrete Umsetzungs-
   übersicht vor — WAS wird implementiert (Stories + Developer Targets), WIE läuft es ab
   (Wellen, Reihenfolge, Fakes, Testkriterien, was bleibt unberührt).
3. **Explizites User-Go** („passt"/„go") — erst DANN Dev + QA starten.

**Verboten:** Dev/QA implizit oder "nebenbei" starten, nur weil eine Anforderung klar
formuliert war. Die Planung kann Änderungen enthalten, die der User erst im Review sieht —
ohne Checkpoint läuft die Maschine gegen dessen Intention (Lesson NetClip 04-01).

**Ausnahme:** Keine — auch vermeintliche Trivialitäten (Text-Änderungen, Einzeiler)
gehen durch den Checkpoint. Der Checkpoint ist billig; ein falscher Lauf ist teuer.

### Phase 0b — Projekt-Setup (Folder + Git)

```bash
mkdir <projekt> && cd <projekt> && git init
# + .gitignore, README.md, opencode.json (lokal), requirements, etc.
```

**Tool-Versionen pinnen (PFLICHT):** Lint-/Test-Tools in `requirements.txt` (o.ä.)
immer **versionsspinnen** (`ruff==0.16.7`, `pytest==8.x.y`), nie ungebunden (`ruff`,
`pytest`). Grund: CI installiert sonst die neueste Version — neue Major-Releases
verschärfen Regeln und die CI wird rot, obwohl lokal alles grün war (Lesson NetClip
07-01: ruff 0.15 lokal vs. 0.16 in CI → 8+ Findings). Laufzeit-Abhängigkeiten (fastapi,
uvicorn …) dürfen dagegen liberal sein, wenn gewünscht — nur die QA-Werkzeuge
müssen lokal == CI sein.

Jede Story = eigener Branch: `feature/<story-id>-<slug>` (z.B. `feature/01-02-cards-crud`).
Kein direkter Push auf `main`/`master`. Merge nur nach QA-Gate.

Siehe `vokabel` als Referenz: `AGENTS.md` + `STORIES.md` + `docs/stories/_template.md`
Siehe `intesis_modbus` als Referenz für Architektur-Trennung.

### Phase 1 — Requirements & Design (Architect, starkes Reasoning — Dokumente IM DIALOG erstellen)

**Agent: `architect` — starkes Modell, lokal konfiguriert via `opencode.jsonc` → `agent.architect.model` — `mode: all` (direkter Dialogpartner, Dokumente entstehen IM DIALOG)**

**Prinzip: Dokumente sind Source of Truth gegen Chat-Drift, aber entstehen IM DIALOG mit dir — nicht autonom im Hintergrund.** (Lessons aus MetaGPT/TraceDev: strukturierte Dokumente verhindern Cascading Hallucinations; RTIA/Coordinated Agent Team: Human Checkpoints)

Ablauf (iterativ, immer mit User-Rückkopplung):

1. **Problem & Zielgruppe** im Dialog klären — architect fragt, du antwortest, er fasst als Entwurf zusammen
2. **Requirements sammeln** — architect entwirft `docs/requirements.md` (mit IDs, siehe Phase 2) als *Vorschlag im Chat*, du reviewst/korrigierst, erst nach deinem "passt so" wird die Datei geschrieben. Jeder Requirement bekommt eine ID `REQ-001`, `REQ-002` (für Traceability).
3. **Architektur-Design entwerfen** → `docs/design.md` als *Vorschlag im Chat* mit:
   - Trennung **Funktion vs Konnektivität** (siehe intesis_modbus/CLAUDE.md)
     - `core/` / `domain/` — reine Regelalgorithmen, null Imports aus Framework/IO. Bekommt alles als Parameter, gibt Dicts/Primitives zurück. Vollständig unit-testbar.
     - `adapters/` / `infra/` — dünner Wrapper: liest Sensoren/APIs/DB, schreibt, delegiert Entscheidungen an Core. 3-10 Zeilen pro Methode.
   - **Fake-Interfaces** zwingend für jede externe Abhängigkeit (Modbus, HA, API, DB, LLM, Zigbee, etc.):
     - `FakeModbus`, `FakeHA`, `FakeOllama`, `Raum`-Simulation wie in `intesis_modbus/tests/raum_simulation.py`
     - Core hat Methoden wie `simuliere_aktiv()` / Simulation-Helpers für Tests
     - `src/adapters/fakes/` oder `tests/fakes/` — explizit im Design dokumentieren
   - Datenmodell, API-Skizze, Deployment (Docker/SQLite/etc.)
   - **Im Dialog vorstellen**, du reviewst, erst nach Freigabe schreiben.
4. **Offene Fragen** sofort im Dialog zurückspielen wenn aussichtslos — nicht raten, nicht in Datei raten.
5. **AGENTS.md** (Repo-Leitplanken) ebenfalls als Dialog-Vorschlag, dann schreiben:
   - **Vorlage nutzen (Pflicht):** Kopiere das Skelett aus `~/.config/opencode/templates/AGENTS.md` — konstante Abschnitte (Workflow, Git-Konvention, Sprachen, Verbote) unverändert lassen, projekt-spezifische Platzhalter (`<...>`) im Dialog ausfüllen (Name, Stack, Kernregeln, Referenzen). Kein Improvisieren von Null.

Regel: Kein `docs/requirements.md` / `docs/design.md` ohne vorherige Dialog-Freigabe. Dokumente frieren den Dialog ein — Chat darf danach nicht mehr driften.

Output nach Freigabe: `docs/requirements.md` (mit REQ-IDs), `docs/design.md`, `AGENTS.md`

### Phase 2 — Features & Stories dekomponieren (IM DIALOG — Traceability)

**Ebenfalls im Dialog mit architect:** Architect schlägt Stories vor, du reviewst, erst nach Freigabe werden Dateien geschrieben. (Human Checkpoint wie RTIA/Coordinated Agent Team)

Output: `STORIES.md` (Index) + `docs/stories/<phase>-<id>-<slug>.md` pro Story

Template pro Story (wie `vokabel/docs/stories/_template.md`, erweitert um Traceability nach TraceDev):

```markdown
# Story <ID> — <Titel>
Status: Geplant | In Arbeit | Erledigt
Traceability: REQ-002, REQ-005 → Design §2.1, §3.3
## Definition
## Entwicklungsziel
## Developer Targets (exakt, nicht mehr/nicht weniger)
## Akzeptanzkriterien (prüft QA-Manager)
## Testkriterien (müssen VOR Implementierung existieren — mit Fake, ohne externe Systeme)
```

Pflichtfelder (QA rejectet Stories ohne diese):
- `Traceability:` — jede Story verlinkt mindestens eine `REQ-XXX` + Design-Abschnitt. Damit erkennt QA fehlende/unimplementierte Requirements (TraceDev-Validator).
- `Testkriterien` müssen Fake-basiert sein (`tests/fakes/`, `Fake*`).

Regeln:
- Stories sind so geschnitten dass **günstige Massenmodelle** (lokal konfiguriert via `agent.developer.model`) sie isoliert **parallel** implementieren können — dein billigstes Modell für repetitive Schreibarbeit. Teures/starkes Modell nur als Fallback für Design/Reasoning (lokal via `agent.architect.model`).
- Jede Story hat eigene Testkriterien → Tests werden ZUERST geschrieben
- Keine unangefragten Features außerhalb der Developer Targets
- Stories erst nach deiner Dialog-Freigabe schreiben — kein autonomes Dekomponieren im Hintergrund
- **Dev+QA starten erst nach dem Planungs-Checkpoint (Phase 0): Doku → User-Review (WAS/WIE) → explizites User-Go → erst dann Developer/QA. Kein implizites Losrennen bei klaren Anforderungen.**

### Phase 3 — Tests zuerst (Test-Cases vor Code)

Vor jedem Dev-Durchlauf: `tests/` + `tests/fakes/` anlegen.

Muster aus `intesis_modbus/tests/`:
- `tests/test_<core>.py` — reine Unit-Tests gegen Core (Fake-Interfaces, keine echten APIs)
- `tests/<domain>_simulation.py` — Szenario-Tests (Raum-Simulation, Lastprofile)
- `tests/fakes/` oder `tests/raum_simulation.py` — Fake-Implementierungen
- `TickSample` / `TickHistory` Pattern für zeitbasierte Logik

### Phase 4 — Implementierung (Developer, günstiges Massenmodell + parallel, per Branch)

**Agent: `developer` — günstiges Massenmodell, lokal konfiguriert via `opencode.jsonc` → `agent.developer.model` — repetive Schreibarbeit, mehrere Developer parallel (so viele, wie dein Budget/Setup erlaubt). Starkes Modell nur als Fallback via architect, nicht für Massen-Implementierung.**

```
git checkout -b feature/<story-id>-<slug>
# Implementiert GENAU die Developer Targets der Story
# Schreibt/erweitert Tests gemäß Testkriterien (mit Fakes, dann pytest ausführen)
# pytest muss grün sein — Output im Commit-Body festhalten
# git commit -m "feat(<id>): <titel>" -m "symbols: <geänderte Export-Symbols> | breaks: <none|breaking> | affects: <abhängige Files> | tests: <pytest grün>"
```

Commit-Template (nach CodeTeam — hilft QA beim Requeue nur betroffener Files, verhindert blinden Full-Rebuild):
```
feat(01-02): cards crud

symbols: Card, CardStore.create | breaks: none | affects: src/adapters/db.py | tests: pytest 12 passed
```

Regeln:
- Ein Developer = ein Branch = eine Story. Nie zwei Agenten auf gleichem Branch/File ohne Koordination.
- Core zuerst, dann Adapter. Fakes bleiben erhalten.
- Kein Überschreiben von fremden Branches.
- Commit-Body MUSS `symbols|breaks|affects|tests` enthalten — QA nutzt das für gezieltes Requeue (CodeTeam-Lesson).

### Phase 5 — QA-Gate (zentraler Qualitätsmanager — deterministischer Richter auf dem günstigen Modell)

**Agent: `qa-manager` — günstiges Modell, lokal konfiguriert via `opencode.jsonc` → `agent.qa-manager.model`. Starkes Modell (via `architect`) nur als Fallback bei unklarer Fehler-/Design-Ursache.**

**Log-Kompression ist deterministisch — kein LLM nötig:** Vor dem QA-Call läuft ein
Wrapper-Skript (`~/.config/opencode/scripts/qa_compress.sh` bzw. Command
`~/.config/opencode/command/qa_summary.md`), das `pytest --tb=short` ausführt und nur
Exit-Code + Fehler-/Testnamen + Assertion extrahiert (≤200 Tokens statt Log-Spam).
Das pytest-Auswerten ist reine Determinisik — der günstige Judge nimmt nur die komprimierte Liste.

**Output strikt JSON-only (keine Monologe, keine Stil-Bewertung, keine Wiederkäuung):**
```json
{"status": "PASS|FAIL|BLOCKED_Design|BLOCKED_Requirements", "reason": "<max 2 Sätze>", "failed_tests": ["<Datei>", ...]}
```

Prüft auf dem Feature-Branch:

1. Requirements eingehalten? (gegen `docs/requirements.md` + Story Akzeptanzkriterien)
2. Tests grün? (`pytest`, `ruff`, `mypy` je nach Projekt)
3. Testabdeckung gemäß Testkriterien?
4. Architektur-Trennung eingehalten? (Core ohne IO-Imports?)
5. Fake-Interfaces vorhanden & genutzt?

**Ergebnis/Status (Autonomie-Konzept — Prozess läuft ohne User, bis Intention relevant):**
- **PASS** → Merge nach `main`/`dev` (squash oder merge, je nach Repo) — nur nach deiner Freigabe
- **FAIL** → Zurück zum Developer mit konkretem Fix-Auftrag (gleicher Branch, Loop). Max. 3 FAIL-Loops, dann BLOCKED.
- **BLOCKED_Design** (Design-Lücke / Architektur trägt nicht: Test un-simulierbar, Story falsch geschnitten, Core/Adapter-Trennung undesignfiziert) → **bleibt AUTONOM, starker Modell-Fallback.** QA delegiert die Ursachenanalyse an `architect` (das lokal konfigurierte starke Modell, nur hier) mit schlanker Diagnose (2-Sätze + komprimierte Testliste, **kein Log-Spam**). Architect revidiert Design minimal-invasiv + Traceability, dann neue Dev-Runde. Nur wenn der Fix wieder scheitert (Autonomie-Budget) → an User.
- **BLOCKED_Requirements** (Fachlichkeit fehlt / Intention-Änderung nötig / nach Autonomie-Budget) → **Eskalation an dich** (präzise Rückfrage, kein Raten). Erst nach deiner Antwort weiter.

**Autonomie-Budget (grenzendose Schleifen verhindern):** Max. 3 Developer-FAIL-Loops je
Story, max. 1-2 architect-Design-Fixes autonom. Greift beides nicht → BLOCKED_Requirements
an User (auch wenn die Ursache technisch scheint — der User entscheidet ob Weitermachen oder Umplanen).

Loop: Developer fixt → QA prüft erneut (nutzt Commit-Body `affects` für gezieltes Requeue) →
bis PASS oder BLOCKED → BLOCKED_Design autonom an architect, BLOCKED_Requirements an dich.

## Git-Branch-Konvention (gegen Überschreiben)

```
main (oder master) — stabil, nur via QA-Gate
dev               — optional, Integration (wie intesis_modbus: master/dev)
feature/00-01-setup
feature/01-01-core-modell
feature/02-03-rating
```

Schutz:
- Kein Agent pusht direkt auf main
- Jeder Agent arbeitet nur auf seinem `feature/*` Branch
- Vor Merge: `git fetch && git rebase origin/main`

## Checkliste für neues Projekt

- [ ] Folder + `git init` + `.gitignore`
- [ ] `AGENTS.md` (aus Phase 1, **aus Vorlage `~/.config/opencode/templates/AGENTS.md`**)
- [ ] `docs/requirements.md`, `docs/design.md`
- [ ] `STORIES.md` + `docs/stories/*.md`
- [ ] `tests/` + `tests/fakes/` + Fake-Interfaces im Design
- [ ] `src/core/` (Funktion) + `src/adapters/` (Konnektivität) Struktur
- [ ] CI: `pytest`, `ruff check`, `mypy` (je nach Stack)
- [ ] **Lint-/Test-Tools versionsspinnen** (`ruff==X.Y.Z`, `pytest==X.Y.Z`) — lokal == CI

## Referenzen im Workspace

- `intesis_modbus/CLAUDE.md` — Trennung Funktion/Konnektivität, Fan-Tick, Modbus-Reset, Simulation
- `intesis_modbus/klimasteuerung.py` — Core ohne HA-Imports, `simuliere_aktiv()`
- `intesis_modbus/klima_geraet.py` — Wrapper 3-10 Zeilen, delegates an Core
- `intesis_modbus/tests/raum_simulation.py` — FakeModbus + Raum-Thermik + SimLoop
- `vokabel/AGENTS.md` — Kern-Features, Architektur-Vorgaben, Workflow Stories
- `vokabel/STORIES.md` — Phasen-Index (Foundation → Curriculum)
- `vokabel/docs/stories/_template.md` — Story-Template
- `luftersteuerung/`, `lufttrockner/` — weitere AppDaemon-Beispiele
