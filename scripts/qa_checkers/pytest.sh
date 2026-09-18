#!/usr/bin/env bash
# pytest checker plugin — registriert sich selbst an der CHECKERS-Registry.
#
# Wird von qa_compress.sh gesourced (nach Registry-Definition). Definiert
# pytest_check() und ruft `register_check pytest pytest_check`.
# Pfad zu qa_compress.sh ist irrelevant — die Registry-Variablen liegen im
# Scope der sourcenden Shell.
#
# Kompakt-Output-Vertrag: pytest_check() gibt das KOMPRIMIERTE Ergebnis auf
# stdout aus und returned den Exit-Code des pytest-Laufs.

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

register_check pytest pytest_check