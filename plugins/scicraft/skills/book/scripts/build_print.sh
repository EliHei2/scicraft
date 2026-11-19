#!/usr/bin/env bash
# Print version: every text color (headings, links, citations, rules, box tints) set to black or gray,
# figures keep their colors, then the color pages are counted for the print shop.
#
# Usage:  bash build_print.sh MAIN.tex COLORS.tex [OUTDIR]
#   COLORS.tex redefines the document's colors (copy assets/print_colors.tex and name your colors).
#   It is input just before \begin{document} of a generated MAIN_print.tex; MAIN.tex is not changed.
#   A color that must survive in print (a ranked results table) is declared with \providecolor in the
#   preamble and left out of COLORS.tex.
# Writes OUTDIR/MAIN_print.pdf (default build_print/) and prints "N color, M black-and-white" with the
# color pages. Needs build.sh and count_color_pages.py beside this script.
set -uo pipefail
[ $# -ge 2 ] && [ "$1" != "-h" ] && [ "$1" != "--help" ] || { sed -n '2,13p' "$0"; exit 0; }
HERE="$(cd "$(dirname "$0")" && pwd)"
MAIN="$1"; COL="$2"; OUT="${3:-build_print}"
JOB="$(basename "$MAIN" .tex)"
PRINT="$(dirname "$MAIN")/${JOB}_print.tex"
grep -q '\\begin{document}' "$MAIN" || { echo "FAILED: no \\begin{document} in $MAIN"; exit 2; }
COLIN="${COL%.tex}"
awk -v col="$COLIN" '/\\begin\{document\}/ && !done {print "\\input{" col "}"; done=1} {print}' "$MAIN" > "$PRINT"
bash "$HERE/build.sh" "$PRINT" "$OUT"; status=$?
rm -f "$PRINT"
[ $status -eq 0 ] || exit $status
python3 "$HERE/count_color_pages.py" "$OUT/${JOB}_print.pdf"
