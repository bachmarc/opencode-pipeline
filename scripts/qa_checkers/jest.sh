#!/usr/bin/env bash
# jest checker plugin — registriert sich selbst an der CHECKERS-Registry.
#
# Wird von qa_compress.sh gesourced (nach Registry-Definition). Definiert
# jest_check() und ruft `register_check jest jest_check`.
# Pfad zu qa_compress.sh ist irrelevant — die Registry-Variablen liegen im
# Scope der sourcenden Shell.
#
# Kompakt-Output-Vertrag: jest_check() gibt das KOMPRIMIERTE Ergebnis auf
# stdout aus und returned den Exit-Code des jest-Laufs.

jest_check() {
  local out codes
  out="$(mktemp)"
  codes="$(mktemp)"
  jest >"$out" 2>&1
  local code=$?
  local summary

  # Ergebniszeile von jest: "Tests:       1 failed, 3 passed, 4 total"
  summary="$(grep -E '^Tests: ' "$out" | tail -n 1)"
  echo "summary: ${summary:-<keine Abschlusszeile>}"

  if [ "$code" -ne 0 ]; then
    echo "## failed_tests"
    grep -E '^✕ ' "$out" | tail -n 20
  fi

  rm -f "$out" "$codes"
  return "$code"
}

register_check jest jest_check