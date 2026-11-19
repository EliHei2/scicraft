#!/usr/bin/env bash
#SBATCH --job-name=[prefix]_unit
#SBATCH --partition=[partition]
#SBATCH --nodes=1
#SBATCH --cpus-per-task=[cores]
#SBATCH --mem=[mem_gb]G
#SBATCH --time=[hh:mm:ss]
#SBATCH --gres=gpu:[gpu type from the site docs]:1
#SBATCH --output=[out_dir]/logs/%x.%j.out
#SBATCH --error=[out_dir]/logs/%x.%j.err
# =============================================================================
# One unit of work on SLURM. The SLURM form of job_lsf.sh. Suggested, not yet
# tested in real work: the author's evidence is all LSF. Check the GPU request
# syntax (--gres type name or --constraint) against the site's documentation.
# Delete the --gres line for a CPU job.
# =============================================================================
set -euo pipefail

PY="[absolute path to the environment's python]"     # never a bare `python`
CODE_SRC="[absolute path to the synced code tree on the cluster]"
CORES="${SLURM_CPUS_PER_TASK:-[cores]}"
UNIT="${UNIT:?launch_units.sh exports UNIT}"
OUT="${OUT:?launch_units.sh exports OUT}"
export PY CODE_SRC

source "${CODE_SRC}/[path to]/job_env.sh"
job_env_export "$CORES"
job_env_provenance
job_env_assert_source [your_package]

UNIT_DIR="${OUT}/${UNIT}"
if [[ -e "${UNIT_DIR}/.done" ]]; then
  echo "job: ${UNIT}: .done present, skipping"
  exit 0
fi
mkdir -p "${UNIT_DIR}"

"$PY" -m [your_package.entry_point] --unit "${UNIT}" --out "${UNIT_DIR}" [other arguments]

test -s "${UNIT_DIR}/[expected output file]" || { echo "job: ${UNIT}: no output" >&2; exit 1; }
date '+%Y-%m-%dT%H:%M:%S' > "${UNIT_DIR}/.done.tmp" && mv "${UNIT_DIR}/.done.tmp" "${UNIT_DIR}/.done"
echo "job: ${UNIT}: done"
