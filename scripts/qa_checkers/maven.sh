#!/usr/bin/env bash
# maven checker plugin — registriert sich selbst an der CHECKERS-Registry.
#
# Wird von qa_compress.sh gesourced (nach Registry-Definition). Definiert
# maven_check() und ruft `register_check maven maven_check`.
# Pfad zu qa_compress.sh ist irrelevant — die Registry-Variablen liegen im
# Scope der sourcenden Shell.
#
# Kompakt-Output-Vertrag: maven_check() gibt das KOMPRIMIERTE Ergebnis auf
# stdout aus und returned den Exit-Code des mvn-Laufs.

maven_check() {
  local out codes
  out="$(mktemp)"
  codes="$(mktemp)"
  mvn test >"$out" 2>&1
  local code=$?
  local summary

  # Ergebniszeile: "Tests run: N, Failures: M, Errors: K, Skipped: S".
  summary="$(grep -E '^Tests run: ' "$out" | tail -n 1)"
  echo "summary: ${summary:-<keine Abschlusszeile>}"

  if [ "$code" -ne 0 ]; then
    echo "## failed_tests"
    # Test identifier steht VOR dem Marker (z.B. "BoardTest.rendersBoard:15 <<< FAILURE!").
    grep -E '<<< FAILURE!' "$out" | tail -n 20
    echo "## short_test_summary"
    grep -E '<<< FAILURE!' "$out" | sed -E 's/ - .*//' | tail -n 20
  fi

  rm -f "$out" "$codes"
  return "$code"
}

register_check maven maven_check