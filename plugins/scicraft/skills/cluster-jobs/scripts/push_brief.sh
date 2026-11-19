#!/usr/bin/env bash
# =============================================================================
# push_brief.sh: send a hand-off brief to the cluster and print the one line to
# paste into the cluster-side agent session. Run on the laptop by the user.
#
#   bash push_brief.sh BRIEF.md HOST REMOTE_DIR [--also FILE]... [--hold FILE]
#                      [--dry-run]
#
#   BRIEF.md     the self-contained brief (assets/handoff_brief.md, filled in)
#   HOST         ssh host alias of a machine that shares the cluster filesystem
#   REMOTE_DIR   where the brief lands on the cluster
#   --also FILE  another file the brief points to (repeatable)
#   --hold FILE  a file sent now that the agent must not open until the brief
#                says so; it is named in the paste line
#   --dry-run    check the files and print the commands, send nothing
#
# Every file must exist and be non-empty, or nothing is sent. One ssh control
# connection is reused, so a key with a passphrase is asked for once. Its
# socket lives in /tmp: socket paths cap at 104 to 108 characters.
# Ported from a working brief-delivery script.
# =============================================================================
set -euo pipefail

usage() { sed -n '3,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 0; }
[[ $# -ge 3 ]] || { usage >&2; exit 64; }
BRIEF="$1"; HOST="$2"; W="$3"; shift 3
FILES=("$BRIEF"); HOLD=""; DRY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --also) FILES+=("${2:?}"); shift 2 ;;
    --hold) HOLD="${2:?}"; FILES+=("$HOLD"); shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 64 ;;
  esac
done
for f in "${FILES[@]}"; do
  [[ -s "$f" ]] || { echo "PUSH FAILED (missing or empty: $f)"; exit 1; }
done
if grep -nE '(^|[[:space:]"=(])\[[A-Za-z][^]]*\]' "$BRIEF" | grep -vE '^\s*[0-9]+:\s*-\s*\[[ x]\]' | head -3 | grep -q .; then
  echo "note: the brief still has [bracketed] text; check these are not unfilled placeholders:"
  grep -nE '(^|[[:space:]"=(])\[[A-Za-z][^]]*\]' "$BRIEF" | head -3
fi

SSH=(ssh -o ControlMaster=auto -o "ControlPath=/tmp/brief-cm-%C" -o ControlPersist=180)
NAME="$(basename "$BRIEF")"
LINE="Read ${W%/}/${NAME} in full and carry it out, starting with stage 0."
[[ -n "$HOLD" ]] && LINE+=" Do not open $(basename "$HOLD") until the brief tells you to."

if ((DRY)); then
  echo "would run: ${SSH[*]} $HOST mkdir -p '$W'"
  echo "would run: rsync -av -e '${SSH[*]}' ${FILES[*]} $HOST:${W%/}/"
  echo "paste line: $LINE"
  exit 0
fi
"${SSH[@]}" "$HOST" "mkdir -p '$W'" || { echo "PUSH FAILED (could not reach $HOST)"; exit 1; }
rsync -av -e "${SSH[*]}" "${FILES[@]}" "$HOST:${W%/}/" || { echo "PUSH FAILED (rsync)"; exit 1; }
echo
echo "sent. Now paste this one line into the cluster session:"
echo "$LINE"
