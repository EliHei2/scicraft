#!/usr/bin/env bash
# Send a brief (and the files it names) to the folder where the receiving agent works,
# then print the one line to paste into that agent's chat.
#
# Ported from the push script of a release hand-off; host, folders and file names are now arguments.
#
# Usage:
#   bash send_brief.sh --host HOST --dest DIR [--first "starting with stage 0"] [--hold FILE] BRIEF [MORE ...]
#   bash send_brief.sh --host local --dest DIR BRIEF            # copy on this machine (for testing)
#   bash send_brief.sh --dry-run --host HOST --dest DIR BRIEF   # print what would run, change nothing
#
#   --host     ssh host as in ~/.ssh/config, or "local"
#   --dest     absolute folder on that host; created if missing
#   --first    words appended to the paste line (default: "starting with stage 0")
#   --hold     a file that is sent but must not be opened yet; named in the paste line
#
# Prints "PUSH FAILED (<reason>)" and exits 1 on any failure. Needs bash, rsync and, for a remote host, ssh.
set -u

HOST="" DEST="" FIRST="starting with stage 0" HOLD="" DRY=0
FILES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --host) HOST="${2:-}"; shift 2 ;;
    --dest) DEST="${2:-}"; shift 2 ;;
    --first) FIRST="${2:-}"; shift 2 ;;
    --hold) HOLD="${2:-}"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"; exit 0 ;;
    -*) echo "PUSH FAILED (unknown option $1)"; exit 1 ;;
    *) FILES+=("$1"); shift ;;
  esac
done

[ -n "$HOST" ] || { echo "PUSH FAILED (no --host)"; exit 1; }
[ -n "$DEST" ] || { echo "PUSH FAILED (no --dest)"; exit 1; }
case "$DEST" in /*) ;; *) echo "PUSH FAILED (--dest must be an absolute path)"; exit 1 ;; esac
[ ${#FILES[@]} -gt 0 ] || { echo "PUSH FAILED (no brief given)"; exit 1; }
[ -z "$HOLD" ] || FILES+=("$HOLD")

for f in "${FILES[@]}"; do
  [ -s "$f" ] || { echo "PUSH FAILED (missing or empty: $f)"; exit 1; }
done

BRIEF_NAME=$(basename "${FILES[0]}")
run() { if [ "$DRY" = 1 ]; then printf '[dry-run] %s\n' "$*"; else "$@"; fi; }

if [ "$HOST" = "local" ]; then
  run mkdir -p "$DEST" || { echo "PUSH FAILED (could not create $DEST)"; exit 1; }
  run rsync -a "${FILES[@]}" "$DEST/" || { echo "PUSH FAILED (rsync)"; exit 1; }
else
  # One ssh connection is reused for mkdir and rsync, so a host that allows one login at a time works.
  # Short socket path: macOS limits unix socket paths to about 104 characters.
  CM="$HOME/.ssh/send-brief-cm-%C"
  SSH_OPTS=(-o ControlMaster=auto -o "ControlPath=$CM" -o ControlPersist=180)
  run ssh "${SSH_OPTS[@]}" "$HOST" "mkdir -p '$DEST'" || { echo "PUSH FAILED (could not reach $HOST)"; exit 1; }
  run rsync -a -e "ssh ${SSH_OPTS[*]}" "${FILES[@]}" "$HOST:$DEST/" || { echo "PUSH FAILED (rsync)"; exit 1; }
fi

LINE="Read $DEST/$BRIEF_NAME in full and carry it out, $FIRST."
[ -z "$HOLD" ] || LINE="$LINE Do not open $(basename "$HOLD") until the brief tells you to."
echo
echo "sent ${#FILES[@]} file(s) to $HOST:$DEST. Now paste this one line into the receiving chat:"
echo "$LINE"
