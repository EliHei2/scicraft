#!/usr/bin/env bash
# Laptop <-> remote sync for a research project. The laptop writes code and prose; the remote computes.
#
#   sync.sh up   [-n] [--exclude PATTERN ...] SRC_DIR  USER@HOST:/path/   code, laptop -> remote
#   sync.sh down [-n] [--exclude PATTERN ...] USER@HOST:/path/  DEST_DIR  results, remote -> laptop
#
# Both directions use rsync -rtvu: -u never overwrites a newer file on the receiving side, and
# --delete is never passed, so nothing on the receiving side is removed. .git never travels: an
# rsync that carried .git back from a remote once overwrote .git/config and the origin remote vanished.
# "up" also leaves out data, runs, results, scratch and caches. "down" refuses to write into a
# folder that holds a .git directory, so results never land in the code tree.
# -n is a dry run (rsync --dry-run). Requires bash and rsync; ssh for remote paths.
set -euo pipefail

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }

[ $# -ge 1 ] || { usage; exit 2; }
case "$1" in -h|--help) usage; exit 0;; up|down) MODE=$1; shift;; *) usage; exit 2;; esac

DRY=()
EXTRA=()
while [ $# -gt 0 ]; do
  case "$1" in
    -n|--dry-run) DRY=(--dry-run); shift;;
    --exclude) EXTRA+=("--exclude=$2"); shift 2;;
    -h|--help) usage; exit 0;;
    --) shift; break;;
    -*) echo "unknown option: $1" >&2; exit 2;;
    *) break;;
  esac
done
[ $# -eq 2 ] || { usage; exit 2; }
SRC=$1; DST=$2
[ -n "$SRC" ] && [ -n "$DST" ] || { echo "empty source or destination" >&2; exit 2; }
# A trailing slash on the source copies its contents, not the folder itself.
case "$SRC" in */) ;; *) SRC="$SRC/";; esac

COMMON=(--exclude=.git --exclude=__pycache__ --exclude='*.pyc' --exclude=.DS_Store)

if [ "$MODE" = up ]; then
  [ -d "$SRC" ] || { echo "source is not a local folder: $SRC" >&2; exit 1; }
  [ -d "$SRC/.git" ] || [ -f "$SRC/CLAUDE.md" ] || [ -f "$SRC/README.md" ] || {
    echo "refusing: $SRC has no .git, CLAUDE.md or README.md; is it really the project root?" >&2; exit 1; }
  rsync -rtvu ${DRY[@]+"${DRY[@]}"} "${COMMON[@]}" \
    --exclude=/data --exclude=/runs --exclude=/results --exclude=/scratch --exclude=/_attic \
    --exclude='*.egg-info' --exclude=.pytest_cache --exclude=.venv ${EXTRA[@]+"${EXTRA[@]}"} "$SRC" "$DST"
else
  case "$DST" in *:*) echo "down writes to a local folder; got $DST" >&2; exit 1;; esac
  mkdir -p "$DST"
  [ ! -d "$DST/.git" ] || { echo "refusing: $DST is a git checkout; pull results into the results tree" >&2; exit 1; }
  rsync -rtvu ${DRY[@]+"${DRY[@]}"} "${COMMON[@]}" ${EXTRA[@]+"${EXTRA[@]}"} "$SRC" "$DST"
fi
echo "sync $MODE done: $SRC -> $DST (rsync -rtvu, no --delete, .git excluded${DRY[0]+, dry run})"
