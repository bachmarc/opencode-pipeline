# Story 01-03 — Framework Self-Checks (tests-first)

Status: Done
Feature: foundation (F-001)

## Context / Purpose

Das Pipeline-Repo hat bisher keine deterministisch prüfbaren Invarianten — QA
(`qa_compress.sh` + Judge) hat nichts, womit es greifen kann. Diese Story führt
pytest-basierte Self-Checks ein, die das Repo gegen sich selbst prüfen.

## Requirements

`pytest tests/` läuft grün und validiert die tragenden Invarianten des Frameworks
(Frontmatter-Disziplin, Rollen-Abstraktion ohne Modellnamen, Template-Konstanz,
Skript-Syntax). Damit wird das Repo QA-bar: `qa_compress.sh` komprimiert den
pytest-Output wie bei jedem Pipeline-Projekt.

## Developer Targets (exactly, no more / no less)

1. `pyproject.toml` anlegen (falls nicht vorhanden): pytest-Konfiguration, `testpaths =
   ["tests"]`, gepinnte pytest-Version in `requirements.txt` (`pytest==<lokale Version>`).
2. `tests/test_framework.py` anlegen mit genau diesen Test-Gruppen:
   - `test_agent_frontmatter()` — für jede `agent/*.md`: YAML-Frontmatter parsbar,
     enthält `description` und `mode`, enthält KEIN `model:` (Modelle nur lokal in
     `opencode.jsonc`).
   - `test_no_model_names_in_portable_files()` — Regex-Scan über `agent/`, `command/`,
     `skills/`, `templates/`, `scripts/` nach konkreten Modell-/Provider-Namen
     (`glm-`, `deepseek`, `qwen`, `haiku`, `claude-`, `ollama-docker`, `:cloud`,
     `anthropic/`); Allowlist für legitime Nennungen (z.B. `intesis_modbus/CLAUDE.md`-
     Dateireferenzen). Treffer → Test-FAIL mit Datei:Zeile.
   - `test_template_exists_and_const()` — `templates/AGENTS.md` existiert; enthält die
     konstanten Abschnitts-Marker: `## Workflow`, `## Git conventions` (bzw. deutsche
     Marker der Vorlage), `## Languages`/`## Sprachen`, `## Prohibitions`/`## Verbote`,
     und mindestens einen `<...>`-Platzhalter.
   - `test_qa_compress_script()` — `bash -n scripts/qa_compress.sh` Exit-Code 0
     (`subprocess`), Datei existiert.
3. Keine Änderungen an bestehenden Dateien außer `pyproject.toml`/`requirements.txt`
   (neu) — keine Prompt-„Verbesserungen", keine README-Edits.

## Acceptance criteria (checked by qa-manager)

- `pytest tests/` grün (alle 4 Test-Gruppen vorhanden und bestanden).
- `pytest` läuft ohne externe Systeme (kein Netz, keine DB — nur stdlib + pytest).
- `bash -n scripts/qa_compress.sh` grün (in Tests enthalten).
- `requirements.txt` pinnt pytest versionsspinnen (Lesson: lokal == CI/QA).

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- Tests werden zuerst geschrieben und müssen initial RED sein (Repository-Invarianten
  verletzen sie noch nicht — daher: Test zuerst committen, dann prüfen, dass `pytest`
  mit den aktuellen Dateien GRÜN ist; ein absichtlich eingefügter Modellname in einer
  portablen Datei muss den Test RED machen — manuell verifizieren, dann zurückbauen).
- Reihenfolge: `tests/test_framework.py` + `pyproject.toml` → `pytest` gegen aktuellen
  Baum (erwartet: GRÜN, da aktuelle Dateien die Invarianten erfüllen) → Negative-Probe
  (temporärer Modellname in `command/implement.md` → RED) → Rückbau → GRÜN.