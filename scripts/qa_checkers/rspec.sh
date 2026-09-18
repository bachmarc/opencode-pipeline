#!/usr/bin/env bash
# rspec checker plugin — registriert sich selbst an der CHECKERS-Registry.
#
# Wird von qa_compress.sh gesourced (nach Registry-Definition). Definiert
# rspec_check() und ruft `register_check rspec rspec_check`.
# Pfad zu qa_compress.sh ist irrelevant — die Registry-Variablen liegen im
# Scope der sourcenden Shell.
#
# Kompakt-Output-Vertrag: rspec_check() gibt das KOMPRIMIERTE Ergebnis auf
# stdout aus und returned den Exit-Code des rspec-Laufs.

rspec_check() {
  local out codes
  out="$(mktemp)"
  codes="$(mktemp)"
  rspec --format progress >"$out" 2>&1
  local code=$?
  local summary

  # Ergebniszeile von rspec: "47 examples, 0 failures" / "2 examples, 1 failure"
  summary="$(grep -E '[0-9]+ examples' "$out" | tail -n 1)"
  echo "summary: ${summary:-<keine Abschlusszeile>}"

  if [ "$code" -ne 0 ]; then
    echo "## failed_tests"
    grep -E '^rspec \./.*#' "$out" | tail -n 20
    echo "## short_test_summary"
    grep -E '^rspec \./.*#' "$out" | sed -E 's/ # .*//' | tail -n 20
  fi

  rm -f "$out" "$codes"
  return "$code"
}

register_check rspec rspec_check