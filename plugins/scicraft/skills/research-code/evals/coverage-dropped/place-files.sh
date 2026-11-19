#!/usr/bin/env bash
# Builds evalkit_repo: a small evaluation harness with four commits and two result folders.
set -eu
H="$(cd "$(dirname "$0")" && pwd)/files/_history"
R="$PWD/evalkit_repo"
mkdir -p "$R"
cd "$R"
git init -q -b main
git config user.name "Eval User"
git config user.email "eval@example.com"
commit() {  # commit <date> <message>
  git add -A
  GIT_AUTHOR_DATE="$1T10:00:00" GIT_COMMITTER_DATE="$1T10:00:00" git commit -q -m "$2"
}
printf 'runs/\n__pycache__/\n' > .gitignore
cp -R "$H/v1/." .
commit 2026-11-03 "Initial evaluation harness"
PYTHONDONTWRITEBYTECODE=1 python3 run.py data/preds.csv runs/2026-11-10 > /dev/null
cp "$H/v2/evalkit/load.py" evalkit/load.py
commit 2026-11-12 "Refactor loader into PredictionReader"
cp "$H/v3/README.md" README.md
commit 2026-11-14 "Add README usage"
cp "$H/v4/evalkit/score.py" evalkit/score.py
commit 2026-11-15 "Speed up scoring"
PYTHONDONTWRITEBYTECODE=1 python3 run.py data/preds.csv runs/2026-11-17 > /dev/null
