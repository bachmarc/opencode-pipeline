---
id: F-014
title: Architecture Checker Evolution
status: planned
owner: ""
req: []
---

## Vision

The deterministic core-purity gate (`scripts/check_architecture.py`) works for any
project layout — not only projects that keep their pure-logic modules inside a
dedicated `src/core/` directory. Projects with root-level files (AppDaemon apps,
single-file cores, flat scripts) get first-class support, and the checker remains
byte-identical for all existing directory-based invocations.

## Context

Real-world project onboarding (F-009 Project Migration) surfaced the case: a project
whose function/connectivity separation is realized as two root-level files
(`intesis_modbus/`: `klimasteuerung.py` = core, `klima_geraet.py` = adapter) instead
of `src/core/` + `src/adapters/` directories. The project is a canonical example of
the separation itself (referenced in the qa-manager prompt), yet `check_architecture.py`
cannot express its core-purity check: it takes a directory argument and rglobs it —
pointing it at the project root would also check the adapter file (which legitimately
imports `appdaemon`/HA) and always FAIL. The current workaround is a hand-rolled
one-liner AST check duplicated in the project's AGENTS.md and story acceptance
criteria — non-deterministic tooling drift, exactly what the pipeline exists to prevent.

Design constraints (from the F-008 polyglot checker discipline):

- **Backward compatible first:** no argument → directory mode, byte-identical behavior.
- **Explicit opt-in:** file-list mode is a new CLI surface, nothing auto-detected.
- **Same contract:** identical violation JSON (`{file, import, line}`), identical
  exit codes, identical PASS/FAIL output schema — existing pinned tests stay green
  unchanged, as with the polyglot rework (12-10).
- **Polyglot from day one:** the file-list mode dispatches per suffix exactly like
  directory mode (`check_architecture()` must not duplicate per-language logic —
  refactor the per-file check into a shared unit used by both modes).

## Stories

- 18-01-check-architecture-file-mode (planned)