#!/usr/bin/env bash
# =============================================================================
# sync_up.sh: laptop to cluster, code only. Run on the laptop.
#
#   bash sync_up.sh SRC_DIR HOST:DEST_DIR [--code-only] [--exclude PATTERN]...
#                   [--stamp] [--marker STRING] [--mirror] [--dry-run]
#
#   -rtvu         recursive, keep times, verbose, and skip files that are newer
#                 on the receiver: never overwrite newer cluster files
#   --delete      refused: on a project tree it wipes cluster-only outputs
#   --mirror      code mirror: rsync -rtv --delete of the code files only, for a
#                 directory that holds code and nothing else (src/). Needs
#                 --code-only and --marker. Removes stale modules that would
#                 otherwise raise ghost errors; excluded files are never deleted.
#                 Prints the far-side __pycache__ cleanup and the symbol check.
#   --code-only   send only *.py *.sh *.yaml *.yml *.toml *.cfg *.json *.txt and
#                 directories, nothing else ("make sure it's just the code files")
#   --exclude P   one more exclude on top of the defaults (repeatable)
#   --stamp       write SRC/CODE_COMMIT (commit, branch, dirty flag) before the
#                 sync, because .git is never sent and the job log must still
#                 name the commit
#   --marker S    after the sync, print the one command that proves the cluster
#                 copy is fresh (grep for a string only the new code contains)
#   --dry-run     rsync -n: list what would move, change nothing
#
# Default excludes: .git __pycache__ *.pyc .DS_Store data runs results
# *.egg-info .pytest_cache .venv. Ported from a working rsync_up script.
# =============================================================================
set -euo pipefail

usage() { sed -n '3,27p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 0; }
[[ $# -ge 2 ]] || { usage >&2; exit 64; }
SRC="$1"; DST="$2"; shift 2
CODE_ONLY=0; STAMP=0; MARKER=""; DRY=0; MIRROR=0; EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --code-only) CODE_ONLY=1; shift ;;
    --exclude) EXTRA+=("--exclude=${2:?}"); shift 2 ;;
    --stamp) STAMP=1; shift ;;
    --marker) MARKER="${2:?}"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    --mirror) MIRROR=1; shift ;;
    --delete*) echo "STOP: --delete is refused: it wipes cluster-side outputs that are not on the laptop (a code-only directory uses --mirror)" >&2; exit 64 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 64 ;;
  esac
done
if ((MIRROR)) && { ((CODE_ONLY == 0)) || [[ -z "$MARKER" ]]; }; then
  echo "STOP: --mirror needs --code-only and --marker: a mirror deletes, so it sends code only and proves what landed" >&2; exit 64
fi
[[ -d "$SRC" ]] || { echo "STOP: source directory not found: $SRC" >&2; exit 64; }
SRC="${SRC%/}/"   # trailing slash: copy the contents, not the folder itself

if ((STAMP)); then
  if git -C "$SRC" rev-parse HEAD >/dev/null 2>&1; then
    {
      echo "commit=$(git -C "$SRC" rev-parse HEAD)"
      echo "branch=$(git -C "$SRC" rev-parse --abbrev-ref HEAD)"
      echo "dirty=$([[ -n "$(git -C "$SRC" status --porcelain)" ]] && echo yes || echo no)"
      echo "stamped=$(date '+%Y-%m-%dT%H:%M:%S')"
    } > "${SRC}CODE_COMMIT"
    echo "stamped ${SRC}CODE_COMMIT: $(head -n1 "${SRC}CODE_COMMIT")"
  else
    echo "note: $SRC is not a git checkout; no CODE_COMMIT written"
  fi
fi

if ((MIRROR)); then ARGS=(-rtv --delete); else ARGS=(-rtvu); fi
ARGS+=(--exclude=.git --exclude=__pycache__ --exclude='*.pyc' --exclude=.DS_Store
      --exclude=data --exclude=runs --exclude=results --exclude='*.egg-info'
      --exclude=.pytest_cache --exclude=.venv)
((${#EXTRA[@]})) && ARGS+=("${EXTRA[@]}")
if ((CODE_ONLY)); then
  ARGS+=(--include='*/' --include='*.py' --include='*.sh' --include='*.yaml' --include='*.yml'
         --include='*.toml' --include='*.cfg' --include='*.json' --include='*.txt'
         --include=CODE_COMMIT --exclude='*' --prune-empty-dirs)
fi
((DRY)) && ARGS+=(-n)

echo "rsync ${ARGS[*]} $SRC $DST"
rsync "${ARGS[@]}" "$SRC" "$DST"

if [[ -n "$MARKER" ]]; then
  host="${DST%%:*}"; dir="${DST#*:}"
  if [[ "$host" == "$DST" ]]; then
    echo "freshness check: grep -rlF '$MARKER' '$dir' | head -3"
  else
    echo "freshness check (run on the cluster): grep -rlF '$MARKER' '$dir' | head -3"
  fi
  if ((MIRROR)); then
    echo "after a mirror (run where the copy lives): find '$dir' -name __pycache__ -type d -prune -exec rm -rf {} +"
    echo "then grep for each symbol the new code defines, for example: grep -rn 'def <new function>' '$dir'"
  fi
fi
