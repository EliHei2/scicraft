#!/usr/bin/env bash
# Text-only PDF for a similarity check (iThenticate and similar upload limits): figures become empty frames,
# text and pagination stay identical. It reuses the full build's aux, bbl, toc, lof, lot and loa files.
#
# Usage:  bash build_textonly.sh MAIN.tex FULL_BUILD_DIR [OUTDIR]
#   Run from the folder that holds MAIN.tex, after a clean build.sh into FULL_BUILD_DIR.
# Writes OUTDIR/MAIN_textonly.pdf (default build_textonly/), prints its size and checks that its page
# count equals the full build's. Regenerate it after every final build.
# Image downsampling (PyMuPDF, Ghostscript /screen) was tried first; the draft-mode build is what worked.
set -uo pipefail
[ $# -ge 2 ] && [ "$1" != "-h" ] && [ "$1" != "--help" ] || { sed -n '2,11p' "$0"; exit 0; }
MAIN="$1"; FULL="$2"; OUT="${3:-build_textonly}"
JOB="$(basename "$MAIN" .tex)"; T="${JOB}_textonly"
[ -f "$FULL/$JOB.pdf" ] || { echo "FAILED: no $FULL/$JOB.pdf; run build.sh first"; exit 2; }
mkdir -p "$OUT"
printf '\\PassOptionsToPackage{draft}{graphicx}\n\\input{%s}\n' "$JOB" > "$T.tex"
for ext in aux bbl toc lof lot loa out; do
  [ -f "$FULL/$JOB.$ext" ] && cp "$FULL/$JOB.$ext" "$OUT/$T.$ext"
done
ok=1
for i in 1 2; do
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$OUT" "$T.tex" > "$OUT/run$i.log" 2>&1 \
    || { tail -20 "$OUT/run$i.log"; ok=0; break; }
done
rm -f "$T.tex"
[ $ok -eq 1 ] || { echo "FAILED: pdflatex"; exit 1; }
a=$(pdfinfo "$FULL/$JOB.pdf" | awk '/^Pages/{print $2}'); b=$(pdfinfo "$OUT/$T.pdf" | awk '/^Pages/{print $2}')
size=$(du -k "$OUT/$T.pdf" | cut -f1)
echo "text-only: $OUT/$T.pdf, ${size} KB, $b pages (full build $a pages)"
[ "$a" = "$b" ] || { echo "FAILED: page count differs from the full build"; exit 1; }
