#!/usr/bin/env bash
# Side build of a LaTeX book with gates: pdflatex, bibtex, pdflatex x3, then counts that must all be zero.
#
# Usage:  bash build.sh MAIN.tex [OUTDIR] [INSTALL_PDF]
#   Run from the folder that holds MAIN.tex (bibliography and figure paths resolve from there).
#   OUTDIR defaults to build/. Build into a scratch folder while anything else edits the tree.
#   INSTALL_PDF, when given, receives the PDF by copy-then-rename, and only when every gate is zero.
#
# Gates: LaTeX errors, undefined references and citations, multiply defined labels, Overfull boxes,
# "Float too large", "too small" (headheight), a remaining "Rerun to get" after the last pass (a clean
# three-pass build once left 64 of 76 contents page numbers wrong), BibTeX warnings, and non-embedded
# fonts (pdffonts, when installed). Prints the page count. Exits 1 when any gate fails.
# Needs: pdflatex, bibtex; pdfinfo and pdffonts (poppler) for pages and fonts.
set -uo pipefail
[ $# -ge 1 ] && [ "$1" != "-h" ] && [ "$1" != "--help" ] || { sed -n '2,15p' "$0"; exit 0; }
MAIN="$1"; OUT="${2:-build}"; INSTALL="${3:-}"
JOB="$(basename "$MAIN" .tex)"
[ -f "$MAIN" ] || { echo "FAILED: $MAIN not found"; exit 2; }
mkdir -p "$OUT"
ROOT="$(pwd)"
run() {
  pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory="$OUT" "$MAIN" \
    > "$OUT/run$1.log" 2>&1 || { tail -30 "$OUT/run$1.log"; echo "FAILED: pdflatex pass $1"; exit 1; }
}
run 1
if grep -q '\\bibdata' "$OUT/$JOB.aux" 2>/dev/null; then
  (cd "$OUT" && BIBINPUTS="$ROOT:" BSTINPUTS="$ROOT:" bibtex "$JOB" > bibtex.log 2>&1) || \
    grep -E "^(I couldn|I found no|Repeated|Warning--I didn)" "$OUT/bibtex.log" | head
fi
for i in 2 3 4; do run "$i"; done
LOG="$OUT/$JOB.log"
count() { grep -cE "$1" "$2" 2>/dev/null || true; }
errors=$(count '^! |^[^:]+:[0-9]+: ' "$LOG")
undef=$(count 'Warning: (Reference|Citation).*undefined' "$LOG")
multi=$(count 'multiply defined' "$LOG")
overfull=$(count '^Overfull' "$LOG")
floatbig=$(count 'Float too large' "$LOG")
small=$(count 'too small' "$LOG")
rerun=$(count 'Rerun to get' "$LOG")
bibw=$(count '^Warning--' "$OUT/bibtex.log")
fonts=0
if command -v pdffonts >/dev/null; then
  fonts=$(pdffonts "$OUT/$JOB.pdf" 2>/dev/null | awk 'NR>2 && $(NF-4)=="no"' | wc -l | tr -d ' ')
fi
pages=?
command -v pdfinfo >/dev/null && pages=$(pdfinfo "$OUT/$JOB.pdf" | awk '/^Pages/{print $2}')
echo "pages $pages | errors $errors | undefined $undef | multiply-defined $multi | overfull $overfull |" \
     "float-too-large $floatbig | too-small $small | rerun $rerun | bibtex-warnings $bibw | fonts-not-embedded $fonts"
grep -E '^Overfull|Warning: (Reference|Citation).*undefined|Float too large|too small' "$LOG" | head -10
bad=$((errors + undef + multi + overfull + floatbig + small + rerun + bibw + fonts))
if [ "$bad" -ne 0 ]; then echo "FAILED: $bad gate hit(s); nothing installed"; exit 1; fi
if [ -n "$INSTALL" ]; then
  cp "$OUT/$JOB.pdf" "$INSTALL.tmp" && mv "$INSTALL.tmp" "$INSTALL" && echo "installed $INSTALL"
fi
echo "clean build: $OUT/$JOB.pdf"
