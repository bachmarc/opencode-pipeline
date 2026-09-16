# opencode-Pipeline

Multi-Agenten-Entwicklungs-Pipeline für Folder-Projekte: **Requirements → Design → Stories → Dev (Flash) → QA-Gate**. Alles als flache, portable opencode-Config gesichert (Config-as-Code).

> **Achtung:** Dieses Repository enthält bewusst **keine `opencode.jsonc`** (Provider-Endpunkte, Modell-Auswahl) und **kein `cron.db`** (lokaler Zustand). Beide bleiben je Rechner **lokal** und sind hier gitignored.

> **Modell-Zuordnung pro Agent:** Die Rollen (`agent/*.md`) tragen **keine** feste `model:`-Zeile mehr. Welches Modell für welchen Zweck läuft, wird **lokal im JSON** unter `agent` konfiguriert (siehe § „Modell-Zuordnung im JSON"). Andere Rechner haben andere Provider/Modellnamen → nur das lokale JSON anpassen, die Rollen-Dateien bleiben unverändert.

---

## Was steckt hier drin — und warum

| Ordner | Inhalt | Warum |
|---|---|---|
| `agent/` | `architect`, `developer`, `qa-manager` | Die drei Rollen der Pipeline als opencode-Agents |
| `skills/dev-workflow/` | `SKILL.md` | Der vollständige, wiederverwendbare Entwicklungs-Workflow |
| `scripts/` | `qa_compress.sh` | Deterministische pytest-Kompression für das QA-Gate |
| `command/` | `qa_summary`, `qa-check`, `status`, `new-project`, `requirements`, `decompose`, `implement` | Aufrufbare Tastenbefehle, die den Ablauf orchestrieren |

Das Ziel ist ein **schlankes, günstiges, autonom laufendes Multi-Agenten-System** — keine verschachtelten LLM-Kaskaden, die Token verbrennen.

---

## Welche Design-Entscheidungen stecken dahinter (das "Wieso")

### 1. Funktions-Trennung: Architect denkt, Developer schreibt, QA prüft

- **architect** (`glm-5.3`, stark) — spricht im Dialog Requirements/Design/Stories aus. Reines Reasoning.
- **developer** (`glm-5.3-flash`/`deepseek-v4-flash`, billig) — implementiert **exakt eine Story** isoliert pro Branch. Viele parallel.
- **qa-manager** (`glm-5.3-flash`) — **deterministischer Richter**, kein Denker. Starkes Modell (`glm-5.3`) nur als **Fallback** via `architect` bei unklarer Fehler-/Design-Ursache.

### 2. Die drei Effizienz-Hebel (Kern des "Warum")

1. **QA abspecken & entlasten** — Kosten-Dämpfer
   - pytest-Logs werden **deterministisch** komprimiert (`qa_compress.sh`, ≤200 Tokens statt 20 000 Log-Spam). **Das Auswerten von pytest braucht kein großes Modell.**
   - QA-Output ist **strikt JSON-only** (`status | reason | failed_tests`), keine Monologe, kein Stil-Geschwätz.
   - Flash-Modell für den QA-Judge; das teure Modell nur bei unklarer Ursache.

2. **Kaskade brechen** — gegen Kontext-Bloat
   - `BLOCKED_Design` → **bleibt autonom**: QA delegiert die Ursachenanalyse an `architect` mit schlanker Diagnose (2 Sätze + komprimierte Testliste, **kein Log-Spam**).
   - `BLOCKED_Requirements` → **Eskalation an User** (nur der User kennt die Intention).
   - Kein automatischer architect-Dispatcher aus QA heraus. Ergebnisse werden **1:1 durchgereicht**, nichts neu formuliert.

3. **Autonomie mit harten Grenzen**
   - Der Prozess läuft lange **ohne User-Interaktion** (Dev-Wellen, QA, Design-Reparatur).
   - **Autonomie-Budget:** max. 3 Developer-FAIL-Loops + max. 1–2 architect-Design-Fixes je Story. Läuft beides ins Leere → **BLOCKED_Requirements an User** (nicht endlos loopen).
   - **Phase-0-Checkpoint:** vor jedem Dev/QA-Start legt der Architect die Umsetzung vor, **erst explizites User-Go** startet die Maschine — außer bei rein technischen Design-Korrekturen.

### 3. Architektur der Projekte, die diese Pipeline baut (aus dem Workflow)

Das eigentliche Pattern hinter allem ist **Funktion vs. Konnektivität**:

- `src/core/` — reine Logik/Regeln, **null Imports** aus Framework/IO/DB/API. Bekommt alles als Parameter, gibt Dicts/Primitives zurück. Vollständig unit-testbar.
- `src/adapters/` — **dünne Wrapper** (3–10 Zeilen): lesen/schreiben externe Schnittstellen, delegieren Entscheidungen ans Core.
- **Fake-Interfaces** sind Pflicht für jede externe Abhängigkeit → Tests laufen ohne echte Systeme.

Daraus folgt: **Tests existieren VOR dem Code**, pro Story gibt es eigene, Fake-basierte Testkriterien.

### 4. Warum Config-as-Code / Git

- Die ganze Pipeline ist nur **flache, lesbare Dateien** (Markdown + ein portables Bash-Skript). Kein Geheimnis, kein Binärformat.
- Dadurch **verschiebbar auf andere Rechner / andere opencode-Installationen**: klonen, fertig. Exec-Bit von `qa_compress.sh` bleibt via Git erhalten.
- **Keine Secrets** in der Config → gefahrlos committen.
- Der einzige maschine-spezifische Teil (`opencode.jsonc`) bleibt bewusst lokal.

---

## Installation auf einem anderen Rechner

```bash
# 1. Repo an die Stelle klonen, wo opencode seine Config erwartet
#    (falls ~/.config/opencode bereits existiert: vorher sichern/leeren)
git clone git@github.com:bachmarc/opencode-pipeline.git ~/.config/opencode

# 2. Pro Rechner LOKAL anlegen (nicht im Repo!): opencode.jsonc
#    mit Provider-Endpunkt (z.B. Ollama baseURL) + Modell-Auswahl.
#    Vorlage siehe unter "Lokale Konfiguration".
```

Danach `opencode` neu starten — Agents, Skills, Commands sind aktiv.

### Lokale Konfiguration (bleibt je Rechner)

Erstelle `~/.config/opencode/opencode.jsonc` (z.B.):

```jsonc
{
  "$schema": "https://opencode.ai",
  "provider": { /* dein Modell-Anbieter, z.B. Ollama via openai-compatible */ },
  "model": "provider/modell",            // Primär-/Dialog-Modell
  "small_model": "provider/modell",      // schlankes Modell (Titel, Zusammenfassungen)
  "agent": {                            // Modell pro Agent (architect/developer/qa-manager)
    "architect":   { "model": "provider/stark"    },
    "developer":   { "model": "provider/flash"    },
    "qa-manager":  { "model": "provider/flash"    }
  },
  "skills": { "paths": ["~/.config/opencode/skills"] }
}
```

> **Nicht** hierher committen — steht in `.gitignore`, weil Host/Provider pro Maschine unterschiedlich sind.

### Wie die Modell-Zuordnung funktioniert ("das Vorgehen im JSON")

Die drei Rollen-Dateien (`agent/architect.md`, `developer.md`, `qa-manager.md`) legen **kein Modell mehr fest** (früher fest verdrahtet als `model:`). Stattdessen gilt eine **Trennung: Rolle vs. Rechner**:

- **Rolle (portabel, im Git):** Wer *was* tut — Modus, Temperatur, Prompt, Regeln. In `agent/*.md`.
- **Rechner (lokal, `.gitignore`d):** *welches Modell* *wofür*. In `~/.config/opencode/opencode.jsonc` unter `agent`.

**Warum:**
- Andere Rechner haben andere APIs/Provider angebunden und andere Modellnamen. War das Modell in der Rollen-Datei hart kodiert, musste man den Rollen-Kern anfassen.
- Jetzt genügt eine **einzige lokale Datei** (`opencode.jsonc`) — Provider-Endpunkte, Modellnamen **und** die `agent`-Zuordnung. Beim Clone auf einem neuen Rechner nur diese Datei anlegen/anpassen, die Rollen bleiben identisch.

**Konkretes Vorgehen je Rechner:**
1. `git clone git@github.com:bachmarc/opencode-pipeline.git ~/.config/opencode`
2. `opencode.jsonc` anlegen (siehe oben) mit deinem Provider + den `agent`-Mapping-Einträgen, die zu deinen verfügbaren Modellen passen.
3. `opencode` **neu starten** — die Config wird beim Start geladen, Änderungen werden nicht hot-reloadet.
4. Wenn ein Mapping-Eintrag fehlt, fällt opencode nicht aus: Ein Agent ohne zugewiesenes Modell nutzt das globale `model` als Default.

---

## Workflow in 60 Sekunden

1. **Neues Projekt:** `/new-project` → Architect-Interview (Requirements, Design, Stories) im Dialog, **Review-Checkpoint mit User-Go**.
2. **Implementieren:** `/implement <story-id>` (Developer) — Tests zuerst, isolierter Branch.
3. **QA-Gate:** `/qa-check <branch>` (QA-Manager) → `qa_compress.sh` komprimiert pytest → JSON-Bewertung.
4. **Status:** `/status` (QA-Manager, Tabelle Story | Branch | Tests | QA | Fehler).
5. **Kompakter QA-Testreport:** `/qa_summary`.

---

## Die drei Agenten im Detail

| | architect | developer | qa-manager |
|---|---|---|---|
| **Rolle** | Requirements-/Design-/Story-Partner, Dialog | Billiger Story-Implementierer | Deterministischer Gatekeeper |
| **Modell** | `glm-5.3:cloud` | `glm-5.3-flash`/`deepseek-v4-flash` | `glm-5.3-flash` (+ `glm-5.3`-Fallback via architect) |
| **Modell-Quelle** | `opencode.jsonc` → `agent.architect.model` | `opencode.jsonc` → `agent.developer.model` | `opencode.jsonc` → `agent.qa-manager.model` |
| **Mode** | `all` (Dialog) | `subagent` | `all` |
| **Output** | Docs / Stories | Branch + Commit | JSON (`PASS/FAIL/BLOCKED_*`) |
| **Budget** | — | 1 Story = 1 Branch | max. 3 FAIL-Loops, dann Eskalation |

---

## Erweitern: neue Testprozesse (`qa_compress.sh` ist modular)

`qa_compress.sh` nutzt ein **Checker-Registry-Pattern**. Jeder Testprozess (pytest, ruff, mypy, …) ist eine Funktion, die ihr Kompaktergebnis auf stdout schreibt und den Exit-Code ihres Unterprozesses returned.

```bash
# 1. Neue Checker-Funktion definieren
mypy_check() { mypy "$@" >/dev/null 2>&1; return $?; }

# 2. Registrieren (aktivieren)
register_check mypy mypy_check
```

Aggregation (Gesamt-FAIL, sobald ein Checker non-zero ist) und Exit-Code passieren automatisch. Zukünftige Testprozesse = eine Funktion + eine Registrierungs-Zeile.

---

## Offene Punkte / Ausblick

- `qa_compress.sh` ist gegen **pytest 9** verifiziert (PASS: `78 passed`; FAIL: `2 failed, 1 passed`); bei älteren pytest-Versionen ggf. eine Zeile im Summary-Grep prüfen.
- Optional: Zusammenführung in ein gemeinsames `~/dotfiles`-Repo mit anderen Tools (dann via Symlink statt Direkt-Klon).
