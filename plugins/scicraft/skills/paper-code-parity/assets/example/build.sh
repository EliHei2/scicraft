#!/bin/bash
# Rebuild every number, table and the PDF from the records. Nothing is re-scored or re-trained here.
#   bash build.sh              (run from this folder; S points at the skill's scripts/)
set -euo pipefail
S=${S:-../../scripts}
PY=${PY:-python3}
"$PY" "$S/gen_macros.py" --spec macros_spec.json --out tables/macros.tex
"$PY" "$S/gen_table.py" --spec table_main.json --out tables/tab_main.tex
"$PY" "$S/check_numbers.py" --spec macros_spec.json --macros tables/macros.tex --claims claims.json --tex paper.tex
"$PY" "$S/verify_contract.py" --actual scoreboard.tsv --reference reference/scoreboard.tsv --vocab vocab.json
mkdir -p build
for i in 1 2; do
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build paper.tex > build/latex.log 2>&1 \
    || { tail -30 build/latex.log; exit 1; }
done
# a gate reads the log, never only the exit code
if grep -E 'undefined|Misplaced' build/latex.log; then echo "LaTeX log has problems"; exit 1; fi
echo "built build/paper.pdf"
