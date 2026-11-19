#!/usr/bin/env bash
# =============================================================================
# track.sh: one snapshot of a fan-out run. Done out of total, which units are
# missing, the live jobs of this run, and log files that carry a known failure.
#
#   bash track.sh --out OUT_DIR [--units UNITS.txt] [--prefix NAME]
#                 [--scheduler lsf|slurm] [--logs LOG_DIR] [--marker .done]
#
#   --out      run directory; unit U is finished when OUT/U/<marker> exists
#   --units    expected unit names, one per line (default: every subdirectory of
#              OUT except logs/ and launch/)
#   --prefix   job-name prefix used at launch (default: basename of OUT)
#   --logs     where job logs land (default: OUT/logs)
#
# Writes OUT/status_snapshot.tsv. Exit 0 when every unit is done, 1 when some
# are missing, 2 when some are missing and a log carries a failure pattern
# (memory or time limit, out of memory, CUDA error, Killed, Traceback). Read the
# log before resubmitting.
# Ported from the status script of a sharded GPU run; the SLURM strings are
# suggested, not yet tested in real work.
# =============================================================================
set -euo pipefail

usage() { sed -n '3,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
OUT=""; UNITS=""; PREFIX=""; SCHED=""; LOGS=""; MARKER=".done"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="${2:?}"; shift 2 ;;
    --units) UNITS="${2:?}"; shift 2 ;;
    --prefix) PREFIX="${2:?}"; shift 2 ;;
    --scheduler) SCHED="${2:?}"; shift 2 ;;
    --logs) LOGS="${2:?}"; shift 2 ;;
    --marker) MARKER="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 64 ;;
  esac
done
[[ -d "$OUT" ]] || { echo "STOP: run directory not found: $OUT" >&2; exit 64; }
OUT="$(cd "$OUT" && pwd)"
PREFIX="${PREFIX:-$(basename "$OUT")}"
LOGS="${LOGS:-${OUT}/logs}"

ALL=()   # bash 3.2 has no mapfile; read line by line
if [[ -n "$UNITS" ]]; then
  while IFS= read -r u; do ALL+=("$u"); done < <(sed -e 's/#.*//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e '/^$/d' "$UNITS")
else
  while IFS= read -r u; do ALL+=("$u"); done < <(find "$OUT" -mindepth 1 -maxdepth 1 -type d ! -name logs ! -name launch -exec basename {} \; | sort)
fi
((${#ALL[@]})) || { echo "STOP: no units found (give --units)" >&2; exit 64; }

SNAP="${OUT}/status_snapshot.tsv"
printf 'unit\tstatus\tfinished_at\n' > "$SNAP"
n_done=0; missing=(); n_missing=0
for u in "${ALL[@]}"; do
  if [[ -e "${OUT}/${u}/${MARKER}" ]]; then
    n_done=$((n_done + 1))
    printf '%s\tdone\t%s\n' "$u" "$(head -n1 "${OUT}/${u}/${MARKER}" 2>/dev/null || true)" >> "$SNAP"
  else
    missing+=("$u"); n_missing=$((n_missing + 1)); printf '%s\tmissing\t-\n' "$u" >> "$SNAP"
  fi
done

echo "run: $OUT"
echo "done: ${n_done} / ${#ALL[@]}"
if ((n_missing)); then
  shown=("${missing[@]:0:20}")
  echo "missing (${n_missing}): ${shown[*]}$( ((n_missing > 20)) && echo ' ...')"
fi
echo "snapshot: $SNAP"

# Live jobs of this run (submit host only).
if [[ "$SCHED" == "lsf" ]] && command -v bjobs >/dev/null 2>&1; then
  echo "live jobs (${PREFIX}_*):"
  bjobs -w -u "${USER}" 2>/dev/null | grep -E "${PREFIX}_" || echo "  none pending or running"
elif [[ "$SCHED" == "slurm" ]] && command -v squeue >/dev/null 2>&1; then
  echo "live jobs (${PREFIX}_*):"
  squeue -h -u "${USER}" -o '%.12i %.9T %.40j %R' 2>/dev/null | grep -E "${PREFIX}_" || echo "  none pending or running"
fi

# Logs with a known failure: the usual suspects on both schedulers.
rc=0
if [[ -d "$LOGS" ]]; then
  PAT='TERM_MEMLIMIT|TERM_RUNLIMIT|OUT_OF_MEMORY|oom-kill|DUE TO TIME LIMIT|OutOfMemory|CUDA error|CUDA out of memory|Killed|Traceback'
  hits="$(grep -rElI "$PAT" "$LOGS" 2>/dev/null | head -10 || true)"
  if [[ -n "$hits" ]]; then
    if ((n_missing)); then echo "logs with a failure pattern (first 10):"
    else echo "logs with a failure pattern (first 10; every unit is done now, so these are earlier attempts):"; fi
    while IFS= read -r f; do
      printf '  %s: %s\n' "$f" "$(grep -oE "$PAT" "$f" | sort -u | tr '\n' ' ')"
    done <<< "$hits"
    ((n_missing)) && rc=2
  fi
fi
if ((rc == 0)) && ((n_missing)); then rc=1; fi
exit "$rc"
