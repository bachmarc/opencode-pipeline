# Story 01-05 — APP_VERSION + Bump Rule

Status: Done
Feature: foundation (F-001)

## Context / Purpose

Die Pipeline-Pflicht `APP_VERSION = "0.1.0"` gilt auch für das Pipeline-Repo selbst —
bisher existiert keine Versionierungs-Anker-Datei.

## Requirements

Repo hat eine version anchor Datei; Regeln für Bumps sind dokumentiert.

## Developer Targets (exactly, no more / no less)

1. `APP_VERSION.py` anlegen: `APP_VERSION = "0.1.0"`.
2. `tests/test_version.py` (oder Erweiterung in `tests/test_framework.py`): Import von
   `APP_VERSION` möglich, Format `X.Y.Z` (semver-Regex), Wert `"0.1.0"`.
3. README: eine Zeile im Deployment-Abschnitt: Version bumpen bei notablen Merges,
   dokumentiert in STORIES.md.

## Acceptance criteria (checked by qa-manager)

- `APP_VERSION.py` existiert mit `APP_VERSION = "0.1.0"`.
- Test prüft Existenz + Format (grün in pytest).

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `test_version.py` zuerst schreiben: Import-Fehler → RED; nach Anlage → GRÜN.