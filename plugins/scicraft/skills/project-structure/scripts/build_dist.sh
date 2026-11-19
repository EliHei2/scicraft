#!/usr/bin/env bash
# Build the distributable zip of one shippable folder from a clean, committed tree.
#
#   build_dist.sh <folder> [--out dist/<folder>.zip]
#   build_dist.sh --help
#
# Refuses to run when `git status --short` is not empty, so the zip holds exactly what a commit holds.
# Builds it with `git archive` from HEAD (tracked files only, so ignored results, caches and generated
# notebooks never enter), then lists the archive beside `git ls-files <folder>` and fails when the two
# differ. Prints the commit, the file count and the size. dist/ belongs in .gitignore: a zip that is
# committed goes stale as soon as the package changes.
#
# Needs bash, git and unzip. Exits 1 on a dirty tree, a folder with no tracked files, or a mismatch.
set -euo pipefail

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }

folder="" out=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --out) out="${2:?--out needs a path}"; shift 2 ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *) folder="${1%/}"; shift ;;
  esac
done
[ -n "$folder" ] || { usage >&2; exit 2; }
[ -n "$out" ] || out="dist/$(basename "$folder").zip"

git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "error: not inside a git repository" >&2; exit 1; }
[ -z "$(git rev-parse --show-prefix)" ] || { echo "error: run from the repository root" >&2; exit 1; }
dirty=$(git status --short)
if [ -n "$dirty" ]; then
  echo "refused: the tree is not clean; commit or stash first, so the zip matches a commit:" >&2
  echo "$dirty" | head -20 >&2
  exit 1
fi
tracked=$(git ls-files -- "$folder" | LC_ALL=C sort)
[ -n "$tracked" ] || { echo "error: no tracked files under $folder" >&2; exit 1; }

mkdir -p "$(dirname "$out")"
rm -f "$out"
git archive --format=zip -o "$out" HEAD -- "$folder"

listed=$(unzip -Z1 "$out" | grep -v '/$' | LC_ALL=C sort)
if [ "$listed" != "$tracked" ]; then
  echo "error: archive and git ls-files differ:" >&2
  diff <(echo "$tracked") <(echo "$listed") >&2 || true
  exit 1
fi
n=$(echo "$tracked" | wc -l | tr -d ' ')
size=$(du -k "$out" | cut -f1)
echo "built $out from commit $(git rev-parse --short HEAD): $n files, ${size} KB; archive matches git ls-files $folder"
echo "next: tell the user what works, what was skipped, and how to upload and run it"
