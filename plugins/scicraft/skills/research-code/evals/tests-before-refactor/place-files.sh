#!/usr/bin/env bash
# Copies featlib_repo and makes it a git repository with one commit.
set -eu
cp -R "$(dirname "$0")/files/." .
cd featlib_repo
git init -q -b main
git config user.name "Eval User"
git config user.email "eval@example.com"
printf '__pycache__/\n.pytest_cache/\n' > .gitignore
git add -A
GIT_AUTHOR_DATE="2026-11-05T09:00:00" GIT_COMMITTER_DATE="2026-11-05T09:00:00" git commit -q -m "Add feature preparation module"
