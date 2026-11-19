#!/usr/bin/env bash
# Copies tabeval_repo and makes it a git repository with one commit on main.
set -eu
cp -R "$(dirname "$0")/files/." .
cd tabeval_repo
git init -q -b main
git config user.name "Eval User"
git config user.email "eval@example.com"
printf 'out/\n__pycache__/\n' > .gitignore
git add -A
GIT_AUTHOR_DATE="2026-11-02T09:00:00" GIT_COMMITTER_DATE="2026-11-02T09:00:00" git commit -q -m "Add predict and summary commands"
