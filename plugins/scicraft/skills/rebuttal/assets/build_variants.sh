#!/bin/bash
# Build the copies of a revised paper from one source, with identical line breaks:
#   <main>.pdf          working copy, with whatever round colors the source turns on (for the authors only)
#   <main>_upload.pdf   every change in the one revision color (the copy to upload)
#   <main>_clean.pdf    no color at all
# Usage:  bash build_variants.sh <main> [fast]
#   <main> is the .tex file name without the extension; "fast" builds the working copy only.
# Environment (optional):
#   TEXPRE='\RequirePackage{shim}'   a line injected before the source, to replace a package missing locally
#                                     without editing the source
#   TEXINPUTS=".:./shim::"            where such a shim lives
# Then compare the copies: python3 <skill>/scripts/rev_pdf_check.py <main>_upload.pdf <main>_clean.pdf
set -e
MAIN="${1:?usage: bash build_variants.sh <main> [fast]}"
MAIN="${MAIN%.tex}"
cd "$(dirname "$MAIN.tex")"
MAIN="$(basename "$MAIN")"
PRE="${TEXPRE:-}"
run() { pdflatex -interaction=nonstopmode -halt-on-error -jobname="$1" "$PRE\\input{$1.tex}" > /dev/null || true; }
full() {
  run "$1"
  if grep -q '\\bibdata' "$1.aux" 2>/dev/null; then bibtex "$1" > /dev/null || true; fi
  run "$1"; run "$1"
}
off_rounds() { sed -e 's/\\shownewtrue/\\shownewfalse/g' -e 's/\\shownewertrue/\\shownewerfalse/g' -e 's/\\shownewesttrue/\\shownewestfalse/g'; }
full "$MAIN"
if [ "$2" != "fast" ]; then
  off_rounds < "$MAIN.tex" > "${MAIN}_upload.tex"
  full "${MAIN}_upload"
  off_rounds < "$MAIN.tex" | sed -e 's/\\revisedcolortrue/\\revisedcolorfalse/g' > "${MAIN}_clean.tex"
  full "${MAIN}_clean"
fi
status=0
for j in "$MAIN" "${MAIN}_upload" "${MAIN}_clean"; do
  [ -f "$j.log" ] || continue
  pages=$( [ -f "$j.pdf" ] && pdfinfo "$j.pdf" 2>/dev/null | awk '/^Pages/{print $2}' )
  undef=$(grep -c -E 'undefined|Citation .* undefined' "$j.log" || true)
  errs=$(grep -c '^!' "$j.log" || true)
  over=$(grep -c '^Overfull' "$j.log" || true)
  echo "$j: ${pages:-no PDF} pages, LaTeX errors $errs, undefined references or citations $undef, overfull boxes $over"
  if [ "$errs" != "0" ] || [ ! -f "$j.pdf" ]; then status=1; fi
done
exit $status
