#!/usr/bin/env bash
# Build a LaTeX document into a scratch folder and gate it: pdflatex, bibtex, pdflatex x3, then count what must be zero.
#
#   bash latex_gate.sh MAIN.tex [OUTDIR] [--pages N] [--allow-overfull] [--no-bib]
#
# MAIN.tex  the root file; the build runs from its folder, so \input paths resolve as they do for the author.
# OUTDIR    scratch build folder (default: build_gate next to MAIN.tex). Never the folder the author reads from:
#           install the PDF only after the gate passes.
# --pages N fail unless the PDF has exactly N pages (a hard page budget, or "chapter starts unchanged").
# --allow-overfull  report overfull boxes without failing on them.
# --no-bib  skip bibtex (a document without a bibliography).
#
# Gate (exit 1 if any fails): no "! " error line, no undefined reference or citation, no "Rerun to get" left in the
# final log (three passes after bibtex left 64 of 76 contents page numbers wrong in one book; the fourth pass is
# here for that reason), no overfull box unless allowed, the page count if asked. Also printed: float-too-large,
# headheight warnings, bibtex warnings, fonts not embedded (pdffonts), page count (pdfinfo).
# Needs pdflatex and bibtex; pdfinfo and pdffonts (poppler) for the page and font lines.
set -u
if [ $# -lt 1 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
  sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi
MAIN="$1"; shift
OUT=""; PAGES=""; ALLOW_OVERFULL=0; BIB=1
while [ $# -gt 0 ]; do
  case "$1" in
    --pages) PAGES="$2"; shift 2 ;;
    --allow-overfull) ALLOW_OVERFULL=1; shift ;;
    --no-bib) BIB=0; shift ;;
    *) OUT="$1"; shift ;;
  esac
done
[ -f "$MAIN" ] || { echo "no such file: $MAIN"; exit 1; }
DIR="$(cd "$(dirname "$MAIN")" && pwd)"; BASE="$(basename "$MAIN" .tex)"
[ -n "$OUT" ] || OUT="$DIR/build_gate"
mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
cd "$DIR" || exit 1

run() {  # one pdflatex pass; on a hard stop show the tail of its log
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$OUT" "$BASE.tex" > "$OUT/run$1.log" 2>&1 \
    || { echo "pdflatex pass $1 stopped:"; tail -30 "$OUT/run$1.log"; exit 1; }
}
run 1
if [ "$BIB" = 1 ] && grep -q '\\bibdata' "$OUT/$BASE.aux" 2>/dev/null; then
  (cd "$OUT" && BIBINPUTS="$DIR:" BSTINPUTS="$DIR:" bibtex "$BASE" > "$OUT/bibtex.log" 2>&1) \
    || grep -E "^(I couldn|Repeated|Warning--I didn)" "$OUT/bibtex.log" | head
fi
for i in 2 3 4; do run "$i"; done

LOG="$OUT/$BASE.log"; PDF="$OUT/$BASE.pdf"; FAIL=0
count() { grep -cE "$1" "$LOG" 2>/dev/null || true; }
ERR=$(count '^! ')
UNDEF=$(count 'Warning: (Reference|Citation).*undefined|There were undefined references')
RERUN=$(count 'Rerun to get')
OVER=$(count '^Overfull')
FLOAT=$(count 'Float too large')
HEAD=$(count 'headheight')
BIBW=0; [ -f "$OUT/bibtex.log" ] && BIBW=$(grep -c '^Warning--' "$OUT/bibtex.log")
NPAGES=$(command -v pdfinfo >/dev/null && pdfinfo "$PDF" 2>/dev/null | awk '/^Pages:/{print $2}')
NOEMB=$(command -v pdffonts >/dev/null && pdffonts "$PDF" 2>/dev/null | awk 'NR>2 && $(NF-4)=="no"' | wc -l | tr -d ' ')

echo "pdf: $PDF"
echo "pages: ${NPAGES:-?}   errors: $ERR   undefined: $UNDEF   rerun: $RERUN   overfull: $OVER"
echo "float too large: $FLOAT   headheight: $HEAD   bibtex warnings: $BIBW   fonts not embedded: ${NOEMB:-?}"
[ "$ERR" -gt 0 ] && { echo "FAIL errors"; grep -E '^! ' "$LOG" | sort | uniq -c | head; FAIL=1; }
[ "$UNDEF" -gt 0 ] && { echo "FAIL undefined references or citations"; grep -E 'undefined' "$LOG" | sort | uniq -c | head; FAIL=1; }
[ "$RERUN" -gt 0 ] && { echo "FAIL still asks for a rerun after four passes"; FAIL=1; }
if [ "$OVER" -gt 0 ]; then
  grep -E '^Overfull' "$LOG" | head
  [ "$ALLOW_OVERFULL" = 1 ] || { echo "FAIL overfull boxes (pass --allow-overfull to report only)"; FAIL=1; }
fi
if [ -n "$PAGES" ] && [ "${NPAGES:-x}" != "$PAGES" ]; then echo "FAIL pages ${NPAGES:-?}, expected $PAGES"; FAIL=1; fi
[ "${NOEMB:-0}" != "0" ] && echo "warn fonts not embedded: see pdffonts $PDF"
[ "$FAIL" = 0 ] && echo "PASS latex gate"
exit "$FAIL"
