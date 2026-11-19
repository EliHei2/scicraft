#!/bin/bash
# push_dist.sh <dist-folder> [commit message]
#
# Pushes a built site (its own git repository, with the remote already set) in small commits: first the page and the
# small files, then the large files two per commit, each push retried. One big push of hundreds of MB tends to fail on
# a slow link; this way every push resumes from what the remote already has, and it is safe to run again.
#
#   BIG_MB=20   files above this size go into the later commits (default 20)
#
# The commit message is plain ("Update preview" by default) and carries no attribution line. Follow the project's own
# rules for commits. Never run this before leak_scan.py is clean.
set -u
case "${1:-}" in -h|--help) sed -n '2,/^set -u/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;; esac
D=${1:?usage: push_dist.sh <dist-folder> [commit message]}
MSG=${2:-Update preview}
BIG_MB=${BIG_MB:-20}
cd "$D" || exit 1
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "not a git repository: $D"; exit 1; }
git remote get-url origin >/dev/null 2>&1 || { echo "no remote named origin in $D"; exit 1; }

push() {
  for i in 1 2 3 4 5; do
    git push -u origin HEAD && return 0
    echo "push retry $i"
  done
  return 1
}
commit() { git diff --cached --quiet || git commit -q -m "$1"; }

# 1. everything except the large files
git add -A -- .
find . -path ./.git -prune -o -type f -size +"${BIG_MB}"M -print | sed 's|^\./||' | while IFS= read -r f; do
  git reset -q -- "$f" 2>/dev/null
done
commit "$MSG"
push || exit 1

# 2. the large files, two per commit
n=0
find . -path ./.git -prune -o -type f -size +"${BIG_MB}"M -print | sed 's|^\./||' | sort | while IFS= read -r f; do
  git add -- "$f"
  n=$((n + 1))
  if [ $((n % 2)) -eq 0 ]; then commit "$MSG (data $((n / 2)))"; push || exit 1; fi
done
git add -A -- .
commit "$MSG (rest)"
push || exit 1

if [ -n "$(git status --porcelain)" ]; then echo "uncommitted changes left"; exit 1; fi
echo "PUSH DONE ($(git log --oneline -1))"
