#!/usr/bin/env bash
# JSON-Syntax-Checker-Plugin — registriert sich selbst an der CHECKERS-Registry.
#
# Wird von qa_compress.sh gesourced (nach Registry-Definition). Definiert
# json_check() und ruft `register_check json json_check`.
#
# Validiert die Syntax ALLER *.json unter dem cwd (QA-geprüftes Projekt) mit
# python3-Stdlib (json). Ausgeschlossen sind die deterministischen Pipeline-
# Verzeichnisse (fester Vertrag, kein Gitignore-Parsing):
#   .git, .pipeline, .worktrees, node_modules, __pycache__,
#   .pytest_cache, dist, build
# sowie die eigene qa_config.json (bereits vom Dispatcher validiert).
#
# Kompakt-Output-Vertrag: json_check() gibt das KOMPRIMIERTE Ergebnis auf
# stdout aus (≤200 Tokens) und returned 0 (alle Dateien valide) oder
# 1 (mind. eine invalide).

json_check() {
  local files invalid
  files="$(mktemp)"
  invalid="$(mktemp)"

  # -type f statt globstar: unabhängig von shopt-Einstellungen der sourcenden
  # Shell (glob-fehlersicher, wie der Plugin-Contract es will).
  find . -type f -name '*.json' \
    -not -path './.git/*' -not -path './.pipeline/*' \
    -not -path './.worktrees/*' -not -path './node_modules/*' \
    -not -path './__pycache__/*' -not -path './.pytest_cache/*' \
    -not -path './dist/*' -not -path './build/*' \
    -not -path './qa_config.json' -print | LC_ALL=C sort >"$files"

  local total=0 count=0 file
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    total=$((total + 1))
    if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$file" >/dev/null 2>&1; then
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

register_check json json_check