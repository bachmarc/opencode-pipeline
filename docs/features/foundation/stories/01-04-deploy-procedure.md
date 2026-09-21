# Story 01-04 — Deploy Procedure (Pull in Live-Clone + Restart)

Status: Done
Feature: foundation (F-001)

## Context / Purpose

Bisher fehlt die dokumentierte Prozedur, wie QA-passierte Änderungen aus dem Dev-Repo in
die Live-Config `~/.config/opencode` kommen. Deployment ist bewusst manuell (Design D2) —
aber es muss schriftlich, reproduzierbar und mit Fallstricken (gitignored Lokaldateien,
Restart-Pflicht) dokumentiert sein.

## Requirements

Jede:r kann (auch auf anderen Rechnern) nachvollziehen, wie eine QA-passierte Version auf
die Maschine kommt — und was dabei nicht kaputtgehen darf (`opencode.jsonc`, `cron.db`).

## Developer Targets (exactly, no more / no less)

1. `README.md` um Abschnitt `## Deployment (dev repo → live config)` ergänzen:
   - Prozedur: `git -C ~/.config/opencode pull origin main` (nur nach QA-PASS-Merge),
     dann opencode **neu starten** (Config wird beim Start geladen, kein Hot-Reload).
   - Hinweis: `opencode.jsonc` und `cron.db` sind gitignored — ein Pull überschreibt sie
     nicht; neue Agent-/Command-/Skill-Dateien erscheinen automatisch.
   - Hinweis: Bei neuen Konfig-Optionen (z.B. `permission.task`) müssen Maschinen ihre
     lokale `opencode.jsonc` einmalig ergänzen (Verweis auf § Model assignment).
   - Rollback: `git -C ~/.config/opencode checkout <tag|hash>` + Neustart.
2. KEINE Automatisierung (kein Deploy-Skript, kein Command) — Design-Entscheidung D2.
3. Keine weiteren README-Umbauten außer diesem Abschnitt.

## Acceptance criteria (checked by qa-manager)

- README enthält den Abschnitt mit Prozedur, Restart-Hinweis, gitignore-Hinweis,
  Rollback.
- Kein Skript/Command für Deployment hinzugefügt (Target 2 eingehalten).

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- Dokumenations-Story: prüfbar via `grep` auf die Abschnitts-Marker in README
  (`## Deployment`, `git pull`, `restart`) — QA prüft Presence, nicht Prosa.