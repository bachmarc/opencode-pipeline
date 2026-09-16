#!/usr/bin/env bash
# QA-Summary: kompakter, modularer Testreport.
# Der QA-Agent liest NIEMALS rohe Logs — nur dieses kompakte Ergebnis.
#
# Modulares Checker-Registry-Pattern:
#   - Jeder Testprozess (pytest, ruff, mypy, ...) ist eine separate Funktion,
#     die sich mit `register_check <name> <funktion>` am Ende registriert.
#   - Jede Check-Funktion gibt auf stdout ihr KOMPRIMIERTES Ergebnis (≤200 Tokens)
#     aus und returned den Exit-Code ihres Unterprozesses.
#   - Das Skript aggregiert: Gesamtstatus = FAIL sobald EIN Checker non-zero ist.
#   - Neue zukünftige Testprozesse = eine neue Funktion + eine register_check-Zeile.
#
# Nutzung: aus dem Projekt-Root aufrufen. Gibt das kompakte QA-Paket aus.

set -uo pipefail

CHECKERS=()

register_check() {
  CHECKERS+=("$1|$2")
}

# --- Checker-Definitionen ---
# Jeder Checker: <name>() -> int (Exit-Code), schreibt Kompakt-Output nach stdout.

pytest_check() {
  local out codes
  out="$(mktemp)"
  codes="$(mktemp)"
  pytest --tb=short >"$out" 2>&1
  local code=$?
  local summary

  # Ergebniszeile von pytest 9: "78 passed, 1 warning" / "1 failed in 0.77s" / "no tests ran"
  summary="$(grep -E '=+ *([0-9]+ )?[0-9,]* *(passed|failed|error|no tests|deselected)' "$out" | tail -n 1)"
  echo "summary: ${summary:-<keine Abschlusszeile>}"

  if [ "$code" -ne 0 ]; then
    echo "## failed_tests"
    grep -E '^(FAILED|ERROR) ' "$out" | tail -n 20
    echo "## short_test_summary"
    grep -E '^(FAILED|ERROR) ' "$out" | sed -E 's/ - .*//' | tail -n 20
    echo "## assertions"
    grep -E '^\s*> *assert' "$out" | tail -n 20
  fi

  rm -f "$out" "$codes"
  return "$code"
}

# Weitere künftige Checker hier anfügen, z.B.:
# ruff_check()  { ruff check  "$@" >/dev/null 2>&1; return $?; }
# mypy_check()  { mypy "$@" >/dev/null 2>&1; return $?; }

# --- Registrierung (aktivieren nach Bedarf) ---
register_check pytest pytest_check
# register_check ruff ruff_check
# register_check mypy mypy_check

# --- Aggregation ---
echo "# QA-Testsummary ($(date +%H:%M:%S))"
echo "---"
overall=0
for entry in "${CHECKERS[@]}"; do
  name="${entry%%|*}"
  fn="${entry##*|}"
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
