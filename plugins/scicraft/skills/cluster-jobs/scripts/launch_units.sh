#!/usr/bin/env bash
# =============================================================================
# launch_units.sh: submit one job per unit (no job arrays), resume-safe, then an
# optional merge job that waits for all of them. Runs on the submit host.
#
#   bash launch_units.sh --scheduler lsf|slurm --job JOB.sh --units UNITS.txt \
#        --out OUT_DIR [--prefix NAME] [--merge MERGE.sh] [--dep ended|done] \
#        [--only UNIT] [--dry-run]
#
#   --job      a job body that reads $UNIT and $OUT (assets/job_lsf.sh, job_slurm.sh)
#   --units    one unit name per line (config id, shard, seed); # comments allowed
#   --out      run directory; a unit is finished when OUT/UNIT/.done exists
#   --prefix   job-name prefix, so the run owns a namespace (default: basename of OUT)
#   --merge    job body submitted after the units, gated on all of them
#   --dep      ended (default): merge starts when every unit ENDED, done or failed,
#              and must itself refuse an incomplete set. done: merge starts only if
#              every unit succeeded; one failed unit leaves it pending forever.
#   --only     submit exactly this one unit, no merge: the calibration run
#   --dry-run  render the per-unit scripts and print the commands, submit nothing
#
# Per unit it skips what is finished (.done) and what is already pending or
# running under the same job name (the merge still waits on it), renders OUT/launch/<run_id>/<unit>.sh with
# UNIT and OUT exported, submits it, and records unit and job id in
# OUT/launch/<run_id>/jobs.tsv. Exit 0 when everything that needed submitting
# was submitted, 1 on a pre-flight or submission failure.
#
# Ported from a working LSF launcher (independent mode: K single-GPU jobs plus a
# gated merge) and the duplicate guard of a campaign submit script. The SLURM
# branch is suggested, not yet tested in real work.
# =============================================================================
set -euo pipefail

usage() { sed -n '3,29p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
log() { printf '[launch %s] %s\n' "$(date '+%H:%M:%S')" "$*"; }

SCHED=""; JOB=""; UNITS=""; OUT=""; PREFIX=""; MERGE=""; DEP="ended"; ONLY=""; DRY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scheduler) SCHED="${2:?}"; shift 2 ;;
    --job) JOB="${2:?}"; shift 2 ;;
    --units) UNITS="${2:?}"; shift 2 ;;
    --out) OUT="${2:?}"; shift 2 ;;
    --prefix) PREFIX="${2:?}"; shift 2 ;;
    --merge) MERGE="${2:?}"; shift 2 ;;
    --dep) DEP="${2:?}"; shift 2 ;;
    --only) ONLY="${2:?}"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (see --help)" ;;
  esac
done

# ---- pre-flight: a typo aborts here, before anything is queued ---------------
[[ "$SCHED" == "lsf" || "$SCHED" == "slurm" ]] || die "--scheduler must be lsf or slurm"
[[ "$DEP" == "ended" || "$DEP" == "done" ]] || die "--dep must be ended or done"
[[ -s "$JOB" ]] || die "job body not found or empty: $JOB"
[[ -s "$UNITS" ]] || die "units file not found or empty: $UNITS"
[[ -n "$OUT" ]] || die "--out is required"
[[ -z "$MERGE" || -s "$MERGE" ]] || die "merge body not found or empty: $MERGE"
bash -n "$JOB" || die "bash -n failed on $JOB"
[[ -z "$MERGE" ]] || bash -n "$MERGE" || die "bash -n failed on $MERGE"
placeholders() {  # lines that still carry a [placeholder] from the templates
  grep -nE '^#(BSUB|SBATCH).*[[:space:]=":]\[[A-Za-z]|^[^#]*(^|[[:space:]"=])\[[A-Za-z][^]]*\]' "$1" \
    | grep -vE '\[\[ | \]\]' || true
}
for f in "$JOB" ${MERGE:+"$MERGE"}; do
  ph="$(placeholders "$f")"
  [[ -z "$ph" ]] || { printf '%s\n' "$ph" | head -5 >&2; die "unfilled [placeholders] in $f (lines above)"; }
done
if [[ "$DRY" == "0" ]]; then
  if [[ "$SCHED" == "lsf" ]]; then command -v bsub >/dev/null || die "bsub not found: run this on the submit host"
  else command -v sbatch >/dev/null || die "sbatch not found: run this on the submit host"; fi
fi
mkdir -p "$OUT" || die "cannot create $OUT"
[[ -w "$OUT" ]] || die "not writable: $OUT"
OUT="$(cd "$OUT" && pwd)"
PREFIX="${PREFIX:-$(basename "$OUT")}"
RUN_ID="$(date '+%Y%m%d_%H%M%S')"
RDIR="${OUT}/launch/${RUN_ID}"
mkdir -p "$RDIR" "${OUT}/logs"
TSV="${RDIR}/jobs.tsv"
printf 'unit\tjob_id\tstatus\n' > "$TSV"

ALL=()   # bash 3.2 has no mapfile; read line by line
while IFS= read -r u; do ALL+=("$u"); done < <(sed -e 's/#.*//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e '/^$/d' "$UNITS")
((${#ALL[@]})) || die "no units in $UNITS"
if [[ -n "$ONLY" ]]; then
  found=0; for u in "${ALL[@]}"; do [[ "$u" == "$ONLY" ]] && found=1; done
  ((found)) || die "--only $ONLY is not in $UNITS"
  ALL=("$ONLY"); MERGE=""
fi
for u in "${ALL[@]}"; do
  [[ "$u" =~ ^[A-Za-z0-9._-]+$ ]] || die "unit name '$u' has characters outside [A-Za-z0-9._-]"
done

# ---- scheduler adapters --------------------------------------------------------
live_id() {  # live_id <job name>: prints the id of a pending or running job of that name
  if [[ "$SCHED" == "lsf" ]]; then
    bjobs -J "$1" -o "jobid stat" -noheader 2>/dev/null | awk '$2=="PEND" || $2=="RUN" {print $1; exit}' || true
  else
    squeue -h -u "${USER}" -n "$1" -o "%i %T" 2>/dev/null | awk '$2 ~ /^(PENDING|RUNNING|CONFIGURING)$/ {print $1; exit}' || true
  fi
}

render() {  # render <template> <unit> <job name> <dest>
  local tpl="$1" unit="$2" name="$3" dest="$4"
  # Directives stay first; exports go right after the directive block.
  awk -v unit="$unit" -v out="$OUT" -v name="$name" '
    BEGIN { injected = 0 }
    /^#BSUB[[:space:]]+-J[[:space:]]/ { print "#BSUB -J " name; next }
    /^#SBATCH[[:space:]]+--job-name=/ { print "#SBATCH --job-name=" name; next }
    {
      if (!injected && NR > 1 && $0 !~ /^#(BSUB|SBATCH)/ ) {
        printf "export UNIT=%c%s%c OUT=%c%s%c\n", 39, unit, 39, 39, out, 39
        injected = 1
      }
      print
    }
    END { if (!injected) printf "export UNIT=%c%s%c OUT=%c%s%c\n", 39, unit, 39, 39, out, 39 }
  ' "$tpl" > "$dest"
  chmod +x "$dest"
}

submit() {  # submit <script> <job name> [dependency ids...] -> prints job id
  local script="$1" name="$2"; shift 2
  local out jid deps="" i
  if [[ "$SCHED" == "lsf" ]]; then
    if (($#)); then
      for i in "$@"; do deps+="${deps:+ && }${DEP}(${i})"; done
      out="$(bsub -J "$name" -w "$deps" < "$script" 2>&1)" || { printf '%s\n' "$out" >&2; return 1; }
    else
      out="$(bsub -J "$name" < "$script" 2>&1)" || { printf '%s\n' "$out" >&2; return 1; }
    fi
    jid="$(printf '%s\n' "$out" | sed -n 's/.*Job <\([0-9][0-9]*\)>.*/\1/p' | head -n1)"
  else
    local kind="afterany"; [[ "$DEP" == "done" ]] && kind="afterok"
    if (($#)); then
      deps="$kind"; for i in "$@"; do deps+=":${i}"; done
      out="$(sbatch --parsable --job-name="$name" --dependency="$deps" "$script" 2>&1)" || { printf '%s\n' "$out" >&2; return 1; }
    else
      out="$(sbatch --parsable --job-name="$name" "$script" 2>&1)" || { printf '%s\n' "$out" >&2; return 1; }
    fi
    jid="$(printf '%s\n' "$out" | tail -n1 | cut -d';' -f1)"
  fi
  [[ "$jid" =~ ^[0-9]+$ ]] || { printf 'could not parse a job id from: %s\n' "$out" >&2; return 1; }
  printf '%s\n' "$jid"
}

# ---- fan out --------------------------------------------------------------------
log "scheduler=$SCHED units=${#ALL[@]} out=$OUT prefix=$PREFIX dep=$DEP dry_run=$DRY"
n_sub=0; n_done=0; n_live=0; ids=(); n_ids=0
for u in "${ALL[@]}"; do
  name="${PREFIX}_${u}"
  if [[ -e "${OUT}/${u}/.done" ]]; then
    n_done=$((n_done + 1)); printf '%s\t-\tdone\n' "$u" >> "$TSV"; continue
  fi
  lid=""; [[ "$DRY" == "0" ]] && lid="$(live_id "$name")"
  if [[ -n "$lid" ]]; then
    # Queued by an earlier launch: not resubmitted, but the merge waits on it too.
    n_live=$((n_live + 1)); ids+=("$lid"); n_ids=$((n_ids + 1))
    printf '%s\t%s\tlive\n' "$u" "$lid" >> "$TSV"
    log "  $u: job $lid named $name is already pending or running, not resubmitting"; continue
  fi
  script="${RDIR}/${u}.sh"
  render "$JOB" "$u" "$name" "$script"
  if [[ "$DRY" == "1" ]]; then
    if [[ "$SCHED" == "lsf" ]]; then log "  would run: bsub -J $name < $script"; else log "  would run: sbatch --parsable --job-name=$name $script"; fi
    printf '%s\t-\tdry-run\n' "$u" >> "$TSV"; n_sub=$((n_sub + 1)); continue
  fi
  jid="$(submit "$script" "$name")" || die "submission failed for unit $u; units before it are on the queue (see $TSV)"
  ids+=("$jid"); n_ids=$((n_ids + 1)); n_sub=$((n_sub + 1))
  printf '%s\t%s\tsubmitted\n' "$u" "$jid" >> "$TSV"
  log "  $u: job $jid"
done

if [[ -n "$MERGE" ]]; then
  mscript="${RDIR}/merge.sh"
  render "$MERGE" "merge" "${PREFIX}_merge" "$mscript"
  if [[ "$DRY" == "1" ]]; then
    log "  would submit the merge after the units with ${DEP}() / $([[ $SCHED == lsf ]] && echo bsub -w || echo sbatch --dependency): $mscript"
  elif [[ -n "$(live_id "${PREFIX}_merge")" ]]; then
    log "  merge NOT submitted: a job named ${PREFIX}_merge is already pending or running"
  elif ((n_ids)); then
    mid="$(submit "$mscript" "${PREFIX}_merge" "${ids[@]}")" || die "merge submission failed"
    printf 'merge\t%s\tsubmitted\n' "$mid" >> "$TSV"
    log "  merge: job $mid, waits on ${n_ids} unit job(s) with ${DEP}()"
  else
    mid="$(submit "$mscript" "${PREFIX}_merge")" || die "merge submission failed"
    printf 'merge\t%s\tsubmitted\n' "$mid" >> "$TSV"
    log "  merge: job $mid (every unit was already done)"
  fi
fi

log "submitted=$n_sub already_done=$n_done already_live=$n_live  record: $TSV"
if [[ -n "$ONLY" && "$DRY" == "0" ]]; then
  log "calibration unit submitted. When it ends, read its peaks before setting resources for the rest:"
  if [[ "$SCHED" == "lsf" ]]; then log "  bjobs -l <job id>   (MAX MEM is host RAM; GPU memory comes from the framework log)"
  else log "  sacct -j <job id> --format=JobID,State,Elapsed,MaxRSS,ReqMem   (GPU memory from the framework log)"; fi
fi
