#!/usr/bin/env bash
# gradle checker plugin — registriert sich selbst an der CHECKERS-Registry.
#
# Wird von qa_compress.sh gesourced (nach Registry-Definition). Definiert
# gradle_check() und ruft `register_check gradle gradle_check`.
# Pfad zu qa_compress.sh ist irrelevant — die Registry-Variablen liegen im
# Scope der sourcenden Shell.
#
# Kompakt-Output-Vertrag: gradle_check() gibt das KOMPRIMIERTE Ergebnis auf
# stdout aus und returned den Exit-Code des gradle-Laufs.

gradle_check() {
  local out codes
  out="$(mktemp)"
  codes="$(mktemp)"
  gradle test >"$out" 2>&1
  local code=$?
  local summary

  # Ergebniszeile: "N tests completed, M failed" (falls vorhanden) oder
  # die BUILD SUCCESSFUL / BUILD FAILED-Zeile.
  summary="$(grep -E 'tests completed|BUILD (SUCCESSFUL|FAILED)' "$out" | tail -n 1)"
  echo "summary: ${summary:-<keine Abschlusszeile>}"

  if [ "$code" -ne 0 ]; then
    echo "## failed_tests"
    # Failing test identifiers (z.B. "com.example.BoardTest > rendersBoard() FAILED");
    # die BUILD FAILED-Zeile selbst ausgeschlossen.
    grep -E 'FAILED$| FAILED' "$out" | grep -v -E '^BUILD FAILED$' | tail -n 20
    echo "## short_test_summary"
    grep -E 'FAILED$| FAILED' "$out" | grep -v -E '^BUILD FAILED$' | sed -E 's/ - .*//' | tail -n 20
  fi

  rm -f "$out" "$codes"
  return "$code"
}

register_check gradle gradle_check