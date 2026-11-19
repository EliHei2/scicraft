#!/usr/bin/env bash
# =============================================================================
# preflight.sh: GPU-free checks before anything is queued. Prints one OK or
# STOP line per check and exits 1 if any STOP. Run it on the submit host, as the
# first line of every command set handed to the user.
#
#   bash preflight.sh --python PY [--src DIR] [--marker STRING] [--module NAME]
#                     [--path P]... [--disk DIR --min-free-gb N]
#
#   --python   absolute interpreter the jobs will call: must exist and run
#   --src      the synced code tree: must exist
#   --marker   a string only the newest code contains: proves the sync landed
#   --module   with --src: `import NAME` under PYTHONPATH=src must resolve inside
#              src (an installed copy shadowing it is a STOP). Skip it for
#              packages that initialize the GPU at import: they hang here.
#   --path     an input that must exist (repeatable)
#   --disk     with --min-free-gb: free space on the filesystem holding DIR
#
# Ported from the pre-flight of a working overnight launcher and the
# "OK or STOP: rsync X from your Mac" one-liner.
# =============================================================================
set -uo pipefail

usage() { sed -n '3,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
PY=""; SRC=""; MARKER=""; MODULE=""; DISK=""; MINFREE=""; PATHS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --python) PY="${2:?}"; shift 2 ;;
    --src) SRC="${2:?}"; shift 2 ;;
    --marker) MARKER="${2:?}"; shift 2 ;;
    --module) MODULE="${2:?}"; shift 2 ;;
    --path) PATHS+=("${2:?}"); shift 2 ;;
    --disk) DISK="${2:?}"; shift 2 ;;
    --min-free-gb) MINFREE="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 64 ;;
  esac
done
[[ -n "$PY" ]] || { usage >&2; exit 64; }

fail=0
ok()   { printf 'OK    %s\n' "$*"; }
stop() { printf 'STOP  %s\n' "$*"; fail=1; }

case "$PY" in
  /*) : ;;
  *) stop "--python must be an absolute path, got '$PY' (a bare python resolves differently per login shell)" ;;
esac
if [[ -x "$PY" ]] && v="$("$PY" -c 'import sys; print(sys.version.split()[0])' 2>&1)"; then
  ok "python $PY ($v)"
else
  stop "python $PY does not run: ${v:-not executable}"
fi

if [[ -n "$SRC" ]]; then
  if [[ -d "$SRC" ]]; then ok "code tree $SRC"; else stop "code tree $SRC missing: sync the code from the laptop first"; fi
  if [[ -f "$SRC/CODE_COMMIT" ]]; then ok "stamped $(head -n1 "$SRC/CODE_COMMIT")"; fi
fi
if [[ -n "$MARKER" ]]; then
  if [[ -n "$SRC" ]] && grep -rqF -- "$MARKER" "$SRC" 2>/dev/null; then
    ok "marker '$MARKER' found: the synced code is the new code"
  else
    stop "marker '$MARKER' not found under ${SRC:-<no --src>}: the cluster has the old code, sync again"
  fi
fi
if [[ -n "$MODULE" && -n "$SRC" && -d "$SRC" ]]; then
  got="$(PYTHONNOUSERSITE=1 PYTHONPATH="$SRC" "$PY" -c "import os,$MODULE as m; print(os.path.realpath(m.__file__))" 2>&1 | tail -n1)"
  want="$(cd "$SRC" && pwd -P)"
  case "$got" in
    "$want"/*) ok "import $MODULE -> $got" ;;
    *) stop "import $MODULE -> $got (expected under $want): an installed copy shadows the synced code, or the import fails" ;;
  esac
fi
for p in "${PATHS[@]+"${PATHS[@]}"}"; do
  if [[ -e "$p" ]]; then ok "input $p"; else stop "input $p missing"; fi
done
if [[ -n "$DISK" && -n "$MINFREE" ]]; then
  free="$(df -Pk "$DISK" 2>/dev/null | awk 'NR==2 {printf "%d", $4/1048576}')"
  if [[ -z "$free" ]]; then stop "cannot read free space on $DISK"
  elif (( free >= MINFREE )); then ok "disk $DISK: ${free} GB free (floor ${MINFREE} GB)"
  else stop "disk $DISK: ${free} GB free, below the floor of ${MINFREE} GB"; fi
fi

if ((fail)); then echo "PREFLIGHT STOP: nothing should be submitted until every line says OK"; exit 1; fi
echo "PREFLIGHT PASS"
