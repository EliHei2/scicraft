#!/usr/bin/env bash
# =============================================================================
# fetch_capped.sh: size-gated, resumable fetch from the cluster that the user
# runs on the laptop in one line (the login needs the user's password or key).
#
#   bash fetch_capped.sh --host HOST --remote-root DIR --dest DIR
#        [--note GLOB]... [--include GLOB]... [--cap-gb N] [--floor-gb N]
#        [--expect-min N] [--source-dir DIR] [--self-test]
#
#   --host H         ssh host alias of a node that shares the cluster filesystem
#   --remote-root D  the remote folder to fetch from
#   --dest D         local folder; created if missing; nothing in it is deleted
#   --note GLOB      a small file fetched first, before any measuring (repeatable)
#   --include GLOB   rsync include pattern for the main fetch (repeatable; parent
#                    directories must be included too, for example 'run1/' and
#                    'run1/*.json'); without one, everything under the root
#   --cap-gb N       stop without downloading if the fetch is over N GB (default 6)
#   --floor-gb N     stop if the fetch would leave under N GB free here (default 6)
#   --expect-min N   after the fetch, at least N files must be in DEST (default 1)
#   --source-dir D   fetch from a local folder instead of HOST (a mock of the
#                    remote tree, to test the script before the real run)
#   --self-test      build a mock tree in a temporary folder, run against it,
#                    check the outcome lines and the cap, and clean up
#
# Ends with "FETCH DONE (N files)" or one line starting "FETCH STOPPED" or
# "FETCH FAILED". Run it again after an interruption: finished files are skipped.
#
# Written for macOS system tools (bash 3.2, rsync 2.6.9, BSD awk and sed). Two
# traps of that rsync broke an earlier fetch script: --partial placed before -e
# swallowed the -e (so --partial is never used), and a grep anchor before \|
# miscounted files (so files are counted with awk). The measuring run and the
# real run share one option array, so the real run does what the dry run showed.
# Ported from a working size-gated fetch script.
# =============================================================================
set -u

usage() { sed -n '3,33p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

HOST=""; ROOT=""; DEST=""; CAP=6; FLOOR=6; EXPECT=1; SRCDIR=""; SELFTEST=0
NOTES=(); INCL=()
while [ $# -gt 0 ]; do
  case "$1" in
    --host) HOST="${2:?}"; shift 2 ;;
    --remote-root) ROOT="${2:?}"; shift 2 ;;
    --dest) DEST="${2:?}"; shift 2 ;;
    --note) NOTES+=("${2:?}"); shift 2 ;;
    --include) INCL+=("${2:?}"); shift 2 ;;
    --cap-gb) CAP="${2:?}"; shift 2 ;;
    --floor-gb) FLOOR="${2:?}"; shift 2 ;;
    --expect-min) EXPECT="${2:?}"; shift 2 ;;
    --source-dir) SRCDIR="${2:?}"; shift 2 ;;
    --self-test) SELFTEST=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 64 ;;
  esac
done

if [ "$SELFTEST" = 1 ]; then
  T=$(mktemp -d "${TMPDIR:-/tmp}/fetchtest.XXXXXX") || exit 1
  mkdir -p "$T/remote/run1" "$T/remote/run2"
  echo "# status" > "$T/remote/STATUS.md"
  for i in 1 2 3; do head -c 2048 /dev/zero > "$T/remote/run1/part$i.bin"; done
  echo '{}' > "$T/remote/run1/meta.json"
  head -c 4096 /dev/zero > "$T/remote/run2/skip.bin"
  me="${BASH_SOURCE[0]}"; fail=0
  out=$(/bin/bash "$me" --source-dir "$T/remote" --dest "$T/local" --note STATUS.md \
        --include 'run1/' --include 'run1/*.bin' --include 'run1/*.json' --expect-min 4 2>&1)
  echo "$out" | tail -n 1 | grep -q '^FETCH DONE (5 files)$' || { echo "self-test: expected FETCH DONE (5 files)"; echo "$out"; fail=1; }
  [ -f "$T/local/run1/part1.bin" ] || { echo "self-test: files landed in the wrong place"; find "$T/local"; fail=1; }
  [ -e "$T/local/run2/skip.bin" ] && { echo "self-test: an excluded file was fetched"; fail=1; }
  out=$(/bin/bash "$me" --source-dir "$T/remote" --dest "$T/local" 2>&1)
  echo "$out" | tail -n 1 | grep -q '^FETCH DONE' || { echo "self-test: rerun did not finish"; fail=1; }
  out=$(/bin/bash "$me" --source-dir "$T/remote" --dest "$T/local2" --floor-gb 999999 2>&1)
  echo "$out" | tail -n 1 | grep -q '^FETCH STOPPED' || { echo "self-test: floor did not stop the fetch"; echo "$out"; fail=1; }
  [ -e "$T/local2/run1" ] && { echo "self-test: something was downloaded after a stop"; fail=1; }
  rm -rf "$T"
  if [ "$fail" = 0 ]; then echo "SELF-TEST PASSED (fetch with includes, rerun, stop at the floor)"; exit 0; fi
  echo "SELF-TEST FAILED"; exit 1
fi

[ -n "$DEST" ] || { echo "FETCH FAILED (--dest is required; see --help)"; exit 64; }
if [ -n "$SRCDIR" ]; then
  SRC="${SRCDIR%/}/"; RSH=()
  echo "== against the local folder $SRC (no login)"
else
  [ -n "$HOST" ] && [ -n "$ROOT" ] || { echo "FETCH FAILED (--host and --remote-root are required; see --help)"; exit 64; }
  SRC="$HOST:${ROOT%/}/"
  # one ssh login for every transfer; the socket stays in /tmp (paths cap at 104 to 108 characters)
  RSH=(-e "ssh -o ControlMaster=auto -o ControlPath=/tmp/fetch-cm-%C -o ControlPersist=300")
fi
mkdir -p "$DEST" || { echo "FETCH FAILED (cannot create $DEST)"; exit 1; }

if [ ${#NOTES[@]} -gt 0 ]; then
  echo "== 1/2 small notes"
  NOPTS=(-av)
  for n in "${NOTES[@]}"; do NOPTS+=("--include=$n"); done
  NOPTS+=("--exclude=*")
  rsync ${RSH[@]+"${RSH[@]}"} "${NOPTS[@]}" "$SRC" "$DEST/" || { echo "FETCH FAILED (notes)"; exit 1; }
fi

OPTS=(-avm)
if [ ${#INCL[@]} -gt 0 ]; then
  for p in "${INCL[@]}"; do OPTS+=("--include=$p"); done
  OPTS+=("--exclude=*")
fi

echo "== 2/2 measuring"
PLAN=$(rsync -n ${RSH[@]+"${RSH[@]}"} "${OPTS[@]}" --stats "$SRC" "$DEST/") || { echo "FETCH FAILED (could not list $SRC)"; exit 1; }
BYTES=$(echo "$PLAN" | sed -n 's/^Total transferred file size: \([0-9,]*\).*/\1/p' | tr -d ',')
if [ -z "$BYTES" ]; then
  echo "$PLAN" | tail -20
  echo "FETCH STOPPED: could not read the size of the download. Nothing downloaded."; exit 1
fi
NFILES=$(echo "$PLAN" | awk '/^Number of files transferred: / {print $NF}' | tr -d ',')
FREE_KB=$(df -k "$DEST" | awk 'NR==2 {print $4}')
NEED_GB=$(( (BYTES + 1073741823) / 1073741824 ))
FREE_GB=$(( FREE_KB / 1048576 ))
echo "   ${NFILES:-?} files to fetch, $BYTES bytes (about $NEED_GB GB); $FREE_GB GB free here"
if [ "$NEED_GB" -gt "$CAP" ] || [ $(( FREE_GB - NEED_GB )) -lt "$FLOOR" ]; then
  echo "FETCH STOPPED: over the cap of $CAP GB or under the floor of $FLOOR GB free. Nothing downloaded."; exit 1
fi

echo "== 2/2 downloading"
rsync ${RSH[@]+"${RSH[@]}"} "${OPTS[@]}" "$SRC" "$DEST/" || { echo "FETCH FAILED (transfer interrupted; run again, finished files are skipped)"; exit 1; }

HAVE=$(find "$DEST" -type f | awk 'END {print NR + 0}')
du -sh "$DEST" | awk '{print "   total here " $1}'
if [ "$HAVE" -lt "$EXPECT" ]; then echo "FETCH STOPPED: $HAVE files in $DEST, at least $EXPECT expected"; exit 1; fi
echo "FETCH DONE ($HAVE files)"
