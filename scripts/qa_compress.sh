#!/usr/bin/env bash
# QA-Summary: kompakter, modularer Testreport.
# Der QA-Agent liest NIEMALS rohe Logs — nur dieses kompakte Ergebnis.
#
# Konfigurierbarkeit (qa_config.json):
#   - Das QA-geprüfte Projekt legt im Projekt-Root (cwd beim Aufruf) eine
#     committete qa_config.json ab: {"checkers": ["<name>", ...]}.
#   - Keine qa_config.json          -> Default ["pytest"] (rückwärtskompatibel).
#   - Unbekannter Checker-Name      -> laut FAIL ("unknown checker: <name>"), Exit 1.
#   - Leere Liste []                -> explizites Opt-out ("no checkers configured
#     (explicit opt-out)"), overall: PASS, Exit 0.
#   - Invalid JSON                  -> FAIL mit Fehlermeldung, Exit 1.
#   - Das Skript darf python3 für JSON-Parsing nutzen (python3 ist Framework-
#     Voraussetzung, nicht Projekt-Voraussetzung).
#
# Modulares Checker-Registry-Pattern mit Plugins:
#   - Jeder Checker ist eine Funktion, die sich mit
#     `register_check <name> <funktion>` am Ende registriert.
#   - Jede Check-Funktion gibt auf stdout ihr KOMPRIMIERTES Ergebnis (≤200 Tokens)
#     aus und returned den Exit-Code ihres Unterprozesses.
#   - Checker leben in Plugin-Dateien unter scripts/qa_checkers/*.sh und
#     registrieren sich selbst. qa_compress.sh sourced nach der Registry-
#     Definition ALLE Plugin-Dateien (sortiert, glob-fehlersicher). Neue Checker
#     = eine neue Plugin-Datei, keine Änderung an qa_compress.sh.
#   - Nur die KONFIGURIERTEN Checker laufen (seriell). Gesamtstatus = FAIL,
#     sobald EIN Checker non-zero ist (AND-Semantik).
#   - Plugin-Dateien werden relativ zum SPEICHERORT dieses Skripts aufgelöst
#     ($(dirname "$0")), nicht zum cwd — der cwd ist das QA-geprüfte Projekt.
#
# Nutzung: aus dem Projekt-Root aufrufen (cwd = QA-geprüftes Projekt).
# Gibt das kompakte QA-Paket aus.

set -uo pipefail

CHECKERS=()

register_check() {
  CHECKERS+=("$1|$2")
}

# --- Plugin-Sourcing (nach Registry-Definition, vor Konfiguration/Ausführung) ---
QA_PLUGINS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/qa_checkers"
shopt -s nullglob
qa_plugins=( "$QA_PLUGINS_DIR"/*.sh )
shopt -u nullglob
for qa_plugin in "${qa_plugins[@]}"; do
  # shellcheck disable=SC1090
  source "$qa_plugin"
done

# --- Konfiguration: Checker-Liste aus qa_config.json (cwd = Projekt-Root) ---
qa_config_file="qa_config.json"
if [ -f "$qa_config_file" ]; then
  # python3 ist Framework-Voraussetzung (nicht Projekt-Voraussetzung).
  # Fehler gehen nach stderr (fail laut, keine Tracebacks), Exit 1.
  configured="$(python3 -c '
import json, sys
try:
    with open("qa_config.json", encoding="utf-8") as fh:
        data = json.load(fh)
except json.JSONDecodeError as exc:
    sys.stderr.write("qa_config.json: invalid JSON: %s\n" % exc)
    sys.exit(1)
except OSError as exc:
    sys.stderr.write("qa_config.json: unreadable: %s\n" % exc)
    sys.exit(1)
if not isinstance(data, dict) or "checkers" not in data:
    sys.stderr.write("qa_config.json: missing key \"checkers\"\n")
    sys.exit(1)
names = data["checkers"]
if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
    sys.stderr.write("qa_config.json: \"checkers\" must be a list of strings\n")
    sys.exit(1)
print(" ".join(names))
')"
  qa_config_status=$?
  if [ "$qa_config_status" -ne 0 ]; then
    exit 1
  fi
else
  configured="pytest"
fi

# Konfigurierte Namen gegen die Registry validieren (unbekannt -> laut FAIL).
for name in $configured; do
  known=0
  for entry in "${CHECKERS[@]}"; do
    if [ "${entry%%|*}" = "$name" ]; then
      known=1
      break
    fi
  done
  if [ "$known" -eq 0 ]; then
    echo "unknown checker: $name (registered: $(printf '%s ' "${CHECKERS[@]%%|*}" | sed 's/ $//'))" >&2
    exit 1
  fi
done

if [ -z "$configured" ]; then
  echo "no checkers configured (explicit opt-out)"
  echo "---"
  echo "overall: PASS"
  exit 0
fi

# --- Aggregation: NUR die konfigurierten Checker, seriell, AND-Semantik ---
echo "# QA-Testsummary ($(date +%H:%M:%S))"
echo "---"
overall=0
for name in $configured; do
  fn=""
  for entry in "${CHECKERS[@]}"; do
    if [ "${entry%%|*}" = "$name" ]; then
      fn="${entry##*|}"
      break
    fi
  done

  buf="$(mktemp)"
  "$fn" >"$buf" 2>&1
  code=$?

  echo "## $name (exit: $code)"
  cat "$buf"
  rm -f "$buf"

  if [ "$code" -ne 0 ]; then
    overall=1
  fi
done

echo "---"
echo "overall: $([ "$overall" -eq 0 ] && echo PASS || echo FAIL)"

exit "$overall"