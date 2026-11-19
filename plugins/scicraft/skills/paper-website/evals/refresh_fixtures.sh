#!/usr/bin/env bash
# Rebuild every case's files/ from the skill's starter and the fictional paper in files/paper.
set -eu
cd "$(dirname "$0")"
python3 make_fixture.py
echo fixtures refreshed
