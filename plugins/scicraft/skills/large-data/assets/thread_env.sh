#!/usr/bin/env bash
# Source this at the top of every heavy job script:  source thread_env.sh [CORES]
#
# Caps every thread pool at the job's core budget, gives the job a short private temp
# directory, and prints what it set. Set these per script, not in a shell profile: a global
# flag added for one tool once broke another tool that needed the opposite setting.
#
# Why each line exists:
#   thread caps      Polars, OpenMP, MKL, OpenBLAS, NumExpr and Rayon each default to one
#                    thread per core. With only OMP_NUM_THREADS set, one job reached 691
#                    threads on a 256-core node and was killed for memory.
#   MALLOC_ARENA_MAX glibc keeps one memory arena per thread; 2 bounds that growth.
#   short TMPDIR     data-loader workers talk over Unix sockets whose path may not exceed
#                    108 characters; a deep or network TMPDIR crashes every worker. Local
#                    disk also avoids stale .nfs files on network storage.

CORES="${1:-${CORES:-4}}"
export CORES
for v in POLARS_MAX_THREADS OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS \
         NUMEXPR_NUM_THREADS RAYON_NUM_THREADS VECLIB_MAXIMUM_THREADS; do
  export "$v=$CORES"
done
export MALLOC_ARENA_MAX=2

# [JOB_ID]: your scheduler's job id variable, or the shell's PID when run by hand.
JOB_TAG="${JOB_ID:-$$}"
export TMPDIR="/tmp/job_${USER:-u}_${JOB_TAG}"
mkdir -p "$TMPDIR"
if [ "${#TMPDIR}" -gt 80 ]; then
  echo "thread_env: TMPDIR is ${#TMPDIR} characters; keep it short (socket paths cap at 108)" >&2
fi
# Remove the temp dir when the job ends, also on failure.
trap 'rm -rf "$TMPDIR"' EXIT

echo "thread_env: CORES=$CORES (all thread pools capped) MALLOC_ARENA_MAX=2 TMPDIR=$TMPDIR" >&2
