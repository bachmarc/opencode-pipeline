#!/usr/bin/env bash
# YAML-Syntax-Checker-Plugin — registriert sich selbst an der CHECKERS-Registry.
#
# Wird von qa_compress.sh gesourced (nach Registry-Definition). Definiert
# yaml_check() und ruft `register_check yaml yaml_check`.
#
# Validiert die Syntax ALLER *.yaml/*.yml unter dem cwd (QA-geprüftes Projekt)
# mit PyYAML (yaml.safe_load). PyYAML ist in requirements.txt gepinnt und
# Framework-Voraussetzung wie python3 — ist es NICHT installierbar, FAILT der
# Checker LAUT (`yaml checker: PyYAML not installed`), nie stilles Überspringen.
#
# Ausgeschlossen sind die deterministischen Pipeline-Verzeichnisse (fester
# Vertrag, kein Gitignore-Parsing):
#   .git, .pipeline, .worktrees, node_modules, __pycache__,
#   .pytest_cache, dist, build
#
# Kompakt-Output-Vertrag: yaml_check() gibt das KOMPRIMIERTE Ergebnis auf
# stdout aus (≤200 Tokens) und returned 0 (alle Dateien valide) oder
# 1 (mind. eine invalide / PyYAML fehlt).

yaml_check() {
  # Lauter FAIL, wenn PyYAML fehlt (nie stilles Überspringen).
  if ! python3 -c "import yaml" >/dev/null 2>&1; then
    echo "yaml checker: PyYAML not installed"
    return 1
  fi

  local files invalid
  files="$(mktemp)"
  invalid="$(mktemp)"

  # -type f statt globstar: unabhängig von shopt-Einstellungen der sourcenden
  # Shell (glob-fehlersicher). *.yaml UND *.yml.
  find . -type f \( -name '*.yaml' -o -name '*.yml' \) \
    -not -path './.git/*' -not -path './.pipeline/*' \
    -not -path './.worktrees/*' -not -path './node_modules/*' \
    -not -path './__pycache__/*' -not -path './.pytest_cache/*' \
    -not -path './dist/*' -not -path './build/*' -print | LC_ALL=C sort >"$files"

  local total=0 count=0 file
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    total=$((total + 1))
    if ! python3 -c "import sys, yaml; yaml.safe_load(open(sys.argv[1]))" "$file" >/dev/null 2>&1; then
      printf 'INVALID %s\n' "${file#./}" >>"$invalid"
      count=$((count + 1))
    fi
  done <"$files"
  rm -f "$files"

  echo "${total} files checked, ${count} invalid"

  if [ "$count" -gt 0 ]; then
    echo "## failed_files"
    tail -n 20 "$invalid"
    rm -f "$invalid"
    return 1
  fi
  rm -f "$invalid"
  return 0
}

register_check yaml yaml_check