#!/usr/bin/env bash
# Nightly run used by the group; do not change the call signature.
set -eu
python3 -m tabeval.cli predict --input data/table.csv --output out/predictions.csv
python3 -m tabeval.cli summary --predictions out/predictions.csv --labels data/table.csv
