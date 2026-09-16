# Story 01-05 — APP_VERSION + Bump Rule

Status: Geplant
Traceability: Design §6 (kein eigenständiges REQ — Konvention aus AGENTS.md-Pflichtteil)

## Definition

Die Pipeline-Pflicht `APP_VERSION = "0.1.0"` gilt auch für das Pipeline-Repo selbst —
bisher existiert keine Versionierungs-Anker-Datei.

## Entwicklungsziel

Repo hat eine version anchor Datei; Regeln für Bumps sind dokumentiert.

## Developer Targets (exakt, nicht mehr/nicht weniger)

1. `APP_VERSION.py` anlegen: `APP_VERSION = "0.1.0"`.
2. `tests/test_version.py` (oder Erweiterung in `tests/test_framework.py`): Import von
   `APP_VERSION` möglich, Format `X.Y.Z` (semver-Regex), Wert `"0.1.0"`.
3. README: eine Zeile im Deployment-Abschnitt: Version bumpen bei notablen Merges,
   dokumentiert in STORIES.md.

## Akzeptanzkriterien (prüft qa-manager)

- `APP_VERSION.py` existiert mit `APP_VERSION = "0.1.0"`.
- Test prüft Existenz + Format (grün in pytest).

## Testkriterien (VOR Implementierung)

- `test_version.py` zuerst schreiben: Import-Fehler → RED; nach Anlage → GRÜN.