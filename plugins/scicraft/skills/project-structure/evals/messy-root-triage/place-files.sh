#!/usr/bin/env bash
# Builds a cluttered project root, ssl_vision/, in the current folder.
set -eu
R=ssl_vision
mkdir -p "$R/src/sslv" "$R/scripts"
echo '"""Self-supervised vision encoder."""' > "$R/src/sslv/__init__.py"
printf '# ssl_vision\n\nSelf-supervised pretraining of a small vision encoder.\n' > "$R/README.md"
for s in 20260301_101500 20260308_093000 20260322_181200 20260410_120000 20260502_074500 20260519_220100; do
  d="$R/runs_$s"; mkdir -p "$d"; printf 'model\ttop1\nvit_s\t0.%s\n' "${s:6:2}" > "$d/scores.tsv"
  touch -t "${s:0:8}1200" "$d/scores.tsv" "$d"
done
cat > "$R/scripts/make_table.py" <<'PY'
"""Build the main results table of the paper from the canonical run."""
import csv
RUN = "runs_20260410_120000"   # the run reported in the paper
with open(f"{RUN}/scores.tsv") as fh:
    rows = list(csv.DictReader(fh, delimiter="\t"))
print(rows)
PY
mkdir -p "$R/final_results" && echo 'old' > "$R/final_results/scores.tsv" && touch -t 202602011200 "$R/final_results/scores.tsv" "$R/final_results"
for d in eval_smoketest eval_tmpcheck2_20260411_101010 eval_submit_test runs_20260410_120000_rerun_check empty_stub; do mkdir -p "$R/$d"; done
echo x > "$R/eval_smoketest/log.txt"
for z in "sslv.zip" "sslv 2.zip" "sslv 3.zip"; do echo zip > "$R/$z"; done
dd if=/dev/zero of="$R/imagenet_subset_backup.tar.gz" bs=1048576 count=6 2>/dev/null
touch "$R/main.aux" "$R/main.log" "$R/notes_misc.txt"
mkdir -p "$R/.venv/bin" && touch "$R/.venv/bin/python"
