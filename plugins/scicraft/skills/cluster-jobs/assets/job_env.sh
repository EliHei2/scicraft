# shellcheck shell=bash
# =============================================================================
# job_env.sh: the per-job environment block. Source it at the top of every job
# body, after the scheduler directives and before any Python runs:
#
#   source "$CODE_SRC/<where you keep it>/job_env.sh"
#   job_env_export 10          # 10 = this job's core budget (-n / --cpus-per-task)
#   job_env_provenance         # host, code commit, GPUs, into the job log
#   job_env_assert_source mypkg   # abort if `import mypkg` is not under $CODE_SRC
#
# Expects CODE_SRC (the synced code tree) and PY (absolute interpreter path) to
# be set by the job body. Works under LSF (LSB_JOBID) and SLURM (SLURM_JOB_ID).
# Ported from a working job library; each line carries the incident behind it.
# =============================================================================

job_env_jobid() { printf '%s\n' "${LSB_JOBID:-${SLURM_JOB_ID:-$$}}"; }

job_env_export() {
  local threads="${1:?job_env_export needs the core budget, e.g. job_env_export 10}"
  # ~/.local packages shadowed the environment's own versions. Set per job, not
  # globally: one script whose dependency lived in ~/.local broke when this was
  # added for another. Install such a dependency into the environment instead.
  export PYTHONNOUSERSITE=1
  # Run the synced tree, not whatever is installed (see job_env_assert_source).
  [[ -n "${CODE_SRC:-}" ]] && export PYTHONPATH="${CODE_SRC}${PYTHONPATH:+:${PYTHONPATH}}"
  # Pin EVERY thread pool to the core budget. A fat node has hundreds of cores;
  # with only OMP set, one job spawned 691 threads and hit its memory limit.
  export OMP_NUM_THREADS="$threads"
  export MKL_NUM_THREADS="$threads"
  export OPENBLAS_NUM_THREADS="$threads"
  export NUMEXPR_NUM_THREADS="$threads"
  export NUMEXPR_MAX_THREADS="$threads"
  export RAYON_NUM_THREADS="$threads"        # Rust thread pools (polars and others)
  export POLARS_MAX_THREADS="$threads"
  # glibc creates one malloc arena per thread; capping them stops resident
  # memory from bloating far past what the program holds.
  export MALLOC_ARENA_MAX=2
  # UCX / CUDA IPC segfaults seen on multi-GPU nodes. Only matters for stacks
  # that use UCX (RAPIDS, Dask-CUDA); harmless elsewhere.
  export UCX_MEMTYPE_CACHE=n
  export UCX_TLS=sm,self
  # Short and node-local. Unix socket paths cap at 108 characters, so a deep
  # TMPDIR crashes DataLoader workers; a TMPDIR on NFS leaves .nfs* files that
  # block cleanup.
  export TMPDIR="${TMPDIR_BASE:-/tmp}/${USER:-u}_$(job_env_jobid)"
  mkdir -p "$TMPDIR"
}

# One block in the log that says where and with what the job ran.
job_env_provenance() {
  printf '[job %s] host=%s\n' "$(job_env_jobid)" "$(hostname)"
  printf '[job %s] python=%s\n' "$(job_env_jobid)" "${PY:-<PY unset>}"
  printf '[job %s] code_src=%s\n' "$(job_env_jobid)" "${CODE_SRC:-<CODE_SRC unset>}"
  # A tree synced without .git loses its commit; the laptop stamps CODE_COMMIT
  # before syncing (sync_up.sh --stamp) so the log can still name it.
  if [[ -n "${CODE_SRC:-}" && -f "${CODE_SRC}/CODE_COMMIT" ]]; then
    printf '[job %s] commit=%s\n' "$(job_env_jobid)" "$(head -n1 "${CODE_SRC}/CODE_COMMIT")"
  fi
  nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv,noheader,nounits 2>/dev/null || true
}

# Abort unless `import <module>` resolves under CODE_SRC. An editable install
# shadowed PYTHONPATH once, and one figure mixed two code versions. Run it inside
# the job: some packages initialize the GPU at import and hang without one.
job_env_assert_source() {
  local module="${1:?job_env_assert_source needs a module name}"
  "${PY:?set PY to the absolute interpreter path}" - "${CODE_SRC:?set CODE_SRC}" "$module" <<'PYEOF'
import importlib, os, sys
want = os.path.realpath(sys.argv[1])
mod = importlib.import_module(sys.argv[2])
got = os.path.realpath(mod.__file__)
if not got.startswith(want + os.sep):
    sys.exit(f"{sys.argv[2]} resolves to {got}\n  expected under: {want}\n"
             "An installed copy is shadowing the synced code. Run in an environment "
             "without that install, or put CODE_SRC first on PYTHONPATH.")
print(f"[job] verified {sys.argv[2]} source: {got}")
PYEOF
}
