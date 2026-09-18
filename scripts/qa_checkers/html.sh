#!/usr/bin/env bash
# HTML-Checker-Plugin — registriert sich selbst an der CHECKERS-Registry.
#
# Wird von qa_compress.sh gesourced (nach Registry-Definition). Definiert
# html_check() und ruft `register_check html html_check`.
#
# Einfache strukturelle Syntax-Pruefung (bewusst "simple" laut Story-Vertrag:
# keine Accessibility-Audits, kein Link-Check, kein JS, kein CSS-Lint).
# Validiert ALLE *.html unter dem cwd (QA-geprueftes Projekt) mit python3-
# Stdlib (html.parser.HTMLParser-Subklasse):
#   - Void-Tags (br, hr, img, input, meta, link, area, base, col, embed,
#     source, track, wbr) brauchen kein Closing und bleiben voellig ausserhalb
#     des Stack-Checks.
#   - Jedes andere Open-Tag kommt auf den Stack; ein Close-Tag muss zum
#     Stack-Top passen (pop). Passt das Close-Tag zu keinem Stack-Eintrag,
#     ist der File invalid: mismatch: expected </A> got </B>. Liegt das
#     Close-Tag tiefer im Stack, schliesst es die darueberliegenden Tags
#     implizit (legal in HTML) — invalid mit: unclosed <tag>.
#   - Bekannte Vereinfachung: `p` ist vom Stack-Check ausgeschlossen
#     (implizites Schliessen ist in HTML legal).
#   - Stack am Dateiende nicht leer -> invalid: unclosed <tag> (innerstes).
#
# Ausgeschlossen sind die deterministischen Pipeline-Verzeichnisse (fester
# Vertrag, kein Gitignore-Parsing):
#   .git, .pipeline, .worktrees, node_modules, __pycache__,
#   .pytest_cache, dist, build
#
# Kompakt-Output-Vertrag: html_check() gibt das KOMPRIMIERTE Ergebnis auf
# stdout aus (≤200 Tokens) und returned 0 (alle Dateien valide) oder
# 1 (mind. eine invalide).

html_check() {
  local files invalid reason
  files="$(mktemp)"
  invalid="$(mktemp)"
  reason="$(mktemp)"

  # -type f statt globstar: unabhaengig von shopt-Einstellungen der
  # sourcenden Shell (glob-fehlersicher, wie der Plugin-Contract es will).
  find . -type f -name '*.html' \
    -not -path './.git/*' -not -path './.pipeline/*' \
    -not -path './.worktrees/*' -not -path './node_modules/*' \
    -not -path './__pycache__/*' -not -path './.pytest_cache/*' \
    -not -path './dist/*' -not -path './build/*' -print | LC_ALL=C sort >"$files"

  local total=0 count=0 file
  while IFS= read -r file; do
    [ -z "$file" ] && continue
    total=$((total + 1))
    if ! python3 - "$file" >"$reason" 2>&1 <<'PYEOF'
import sys
from html.parser import HTMLParser

VOID_TAGS = frozenset((
    "br", "hr", "img", "input", "meta", "link", "area", "base",
    "col", "embed", "source", "track", "wbr",
))
# Documented simplification: implicit close of <p> is legal in HTML, so p
# is excluded from the stack check.
NO_STACK_TAGS = frozenset(("p",))


class StackParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.reason = ""

    def handle_starttag(self, tag, attrs):
        if tag not in VOID_TAGS and tag not in NO_STACK_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID_TAGS or tag in NO_STACK_TAGS:
            return
        if not self.stack:
            if not self.reason:
                self.reason = "mismatch: unexpected </%s> (stack empty)" % tag
            return
        if tag == self.stack[-1]:
            self.stack.pop()
            return
        if tag in self.stack:
            # Implicit close: the close tag sits deeper in the stack, so all
            # tags above it were never closed explicitly.
            if not self.reason:
                self.reason = "unclosed " + self.stack[-1]
            while self.stack:
                if self.stack.pop() == tag:
                    break
            return
        if not self.reason:
            self.reason = "mismatch: expected </%s> got </%s>" % (
                self.stack[-1], tag,
            )


try:
    with open(sys.argv[1], encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    parser = StackParser()
    parser.feed(text)
    parser.close()
except Exception:
    sys.stderr.write("parse error\n")
    sys.exit(1)

if parser.reason:
    sys.stderr.write(parser.reason + "\n")
    sys.exit(1)
if parser.stack:
    sys.stderr.write("unclosed " + parser.stack[-1] + "\n")
    sys.exit(1)

sys.exit(0)
PYEOF
    then
      printf 'INVALID %s (%s)\n' "${file#./}" "$(head -n 1 "$reason")" >>"$invalid"
      count=$((count + 1))
    fi
  done <"$files"
  rm -f "$files" "$reason"

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

register_check html html_check