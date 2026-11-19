#!/usr/bin/env bash
# =============================================================================
# pull_results.sh: the return half of push_brief.sh. Copies what the
# cluster-side agent wrote to its outbox into a local inbox. Run on the laptop.
#
#   bash pull_results.sh HOST REMOTE_DIR LOCAL_INBOX [--dry-run]
#   bash pull_results.sh --self-test
#
#   HOST         ssh host alias of a node that shares the cluster filesystem,
#                or "-" to read REMOTE_DIR as a local folder (for testing)
#   REMOTE_DIR   the outbox the cluster session writes to; must hold STATUS.md
#   LOCAL_INBOX  local folder whose path has a component named "inbox"
#                (results/inbox, inbox/round2); anything else is refused, so a
#                pull can never land on the working tree
#   --dry-run    list what would be copied, copy nothing
#
# Only new or changed files move (rsync -rtu: a local file that is newer is
# kept). Nothing is deleted on either side. The first 40 lines of STATUS.md are
# printed. rsync keeps the remote modification times, so find what just arrived
# by change time: touch a stamp file before the pull, then
# find LOCAL_INBOX -cnewer STAMP -type f.
# Ends with "PULL DONE: N files" or one line starting "PULL STOPPED".
# Ported from a working pull script (which used a cloud-drive copy tool).
# =============================================================================
set -u

usage() { sed -n '3,23p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
[ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] && { usage; exit 0; }

if [ "${1:-}" = "--self-test" ]; then
  T=$(mktemp -d "${TMPDIR:-/tmp}/pulltest.XXXXXX") || exit 1
  me="${BASH_SOURCE[0]}"; fail=0
  mkdir -p "$T/out/tables" "$T/res/inbox"
  printf '# STATUS\ngate A: 0.91\n' > "$T/out/STATUS.md"
  echo "a,b" > "$T/out/tables/t1.csv"
  echo "mine" > "$T/res/inbox/local_only.txt"
  o=$(/bin/bash "$me" - "$T/out" "$T/res/inbox" 2>&1)
  echo "$o" | tail -n 1 | grep -q '^PULL DONE: 2 files$' || { echo "self-test: first pull"; echo "$o"; fail=1; }
  [ -f "$T/res/inbox/local_only.txt" ] || { echo "self-test: a local file was deleted"; fail=1; }
  echo "$o" | grep -q 'gate A: 0.91' || { echo "self-test: STATUS.md head not printed"; fail=1; }
  o=$(/bin/bash "$me" - "$T/out" "$T/res/inbox" 2>&1)
  echo "$o" | tail -n 1 | grep -q '^PULL DONE: 0 files$' || { echo "self-test: second pull copied again"; echo "$o"; fail=1; }
  o=$(/bin/bash "$me" - "$T/out" "$T/res" 2>&1)
  echo "$o" | tail -n 1 | grep -q '^PULL STOPPED' || { echo "self-test: destination outside an inbox accepted"; fail=1; }
  rm "$T/out/STATUS.md"; mkdir -p "$T/res/inbox2/inbox"
  o=$(/bin/bash "$me" - "$T/out" "$T/res/inbox2/inbox" 2>&1)
  echo "$o" | tail -n 1 | grep -q '^PULL STOPPED: no STATUS.md found, nothing copied$' || { echo "self-test: missing STATUS.md"; echo "$o"; fail=1; }
  [ -e "$T/res/inbox2/inbox/tables" ] && { echo "self-test: copied without STATUS.md"; fail=1; }
  rm -rf "$T"
  if [ "$fail" = 0 ]; then echo "SELF-TEST PASSED (copy, no delete, no recopy, inbox guard, STATUS.md guard)"; exit 0; fi
  echo "SELF-TEST FAILED"; exit 1
fi

[ $# -ge 3 ] || { usage >&2; exit 64; }
HOST="$1"; RDIR="${2%/}"; INBOX="${3%/}"; shift 3
DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1; shift ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 64 ;;
  esac
done

case "/$INBOX/" in
  */inbox/*) ;;
  *) echo "PULL STOPPED: $INBOX has no path component named inbox; nothing copied"; exit 1 ;;
esac
case "/$INBOX/" in
  */../*) echo "PULL STOPPED: $INBOX contains '..'; give the inbox path directly; nothing copied"; exit 1 ;;
esac
mkdir -p "$INBOX" || { echo "PULL STOPPED: cannot create $INBOX"; exit 1; }

if [ "$HOST" = "-" ]; then
  SRC="$RDIR/"; RSH=()
  [ -f "$RDIR/STATUS.md" ] || { echo "PULL STOPPED: no STATUS.md found, nothing copied"; exit 1; }
else
  SRC="$HOST:$RDIR/"
  SSHC="ssh -o ControlMaster=auto -o ControlPath=/tmp/pull-cm-%C -o ControlPersist=180"
  RSH=(-e "$SSHC")
  $SSHC "$HOST" "test -f '$RDIR/STATUS.md'" || { echo "PULL STOPPED: no STATUS.md found, nothing copied"; exit 1; }
fi

OPTS=(-rtu --out-format='%n')
[ "$DRY" = 1 ] && OPTS+=(-n)
LIST=$(rsync ${RSH[@]+"${RSH[@]}"} "${OPTS[@]}" "$SRC" "$INBOX/") || { echo "PULL STOPPED: rsync failed; run again, copied files are skipped"; exit 1; }
N=$(printf '%s\n' "$LIST" | awk 'NF && $0 !~ /\/$/ {n++} END {print n + 0}')
[ -n "$LIST" ] && printf '%s\n' "$LIST" | awk 'NF && $0 !~ /\/$/' | head -50

if [ -f "$INBOX/STATUS.md" ]; then
  echo; echo "== STATUS.md (first 40 lines)"; head -n 40 "$INBOX/STATUS.md"; echo
fi
if [ "$DRY" = 1 ]; then echo "PULL DONE: $N files (dry run, nothing copied)"; else echo "PULL DONE: $N files"; fi
