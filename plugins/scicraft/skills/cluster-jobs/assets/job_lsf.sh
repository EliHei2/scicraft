#!/usr/bin/env bash
#BSUB -J [prefix]_unit
#BSUB -q [queue]
#BSUB -n [cores]
#BSUB -R "rusage[mem=[mem_gb]G] span[hosts=1]"
#BSUB -M [mem_gb]G
#BSUB -W [hh:mm]
#BSUB -gpu "num=1:j_exclusive=[yes or no, per site policy]:gmodel=[gpu model string from the site docs]"
#BSUB -o [out_dir]/logs/%J.out
#BSUB -e [out_dir]/logs/%J.err
# =============================================================================
# One unit of work (one config, one shard, one seed) on LSF. launch_units.sh
# renders one copy per unit with UNIT and OUT exported and the job name set.
# Delete the -gpu line for a CPU job. Measured numbers go in the brackets:
# calibrate on one unit first (SKILL.md section 4).
# =============================================================================
set -euo pipefail

PY="[absolute path to the environment's python]"     # never a bare `python`
CODE_SRC="[absolute path to the synced code tree on the cluster]"
CORES=[cores]                                         # same number as -n above
UNIT="${UNIT:?launch_units.sh exports UNIT}"
OUT="${OUT:?launch_units.sh exports OUT}"
export PY CODE_SRC

source "${CODE_SRC}/[path to]/job_env.sh"
job_env_export "$CORES"
job_env_provenance
job_env_assert_source [your_package]

UNIT_DIR="${OUT}/${UNIT}"
# Resume-safe: a finished unit is skipped, so rerunning the launcher only
# resubmits what is missing.
if [[ -e "${UNIT_DIR}/.done" ]]; then
  echo "job: ${UNIT}: .done present, skipping"
  exit 0
fi
mkdir -p "${UNIT_DIR}"

"$PY" -m [your_package.entry_point] --unit "${UNIT}" --out "${UNIT_DIR}" [other arguments]

# The sentinel is written last and only after the output is checked, so a
# killed job never leaves a .done behind.
test -s "${UNIT_DIR}/[expected output file]" || { echo "job: ${UNIT}: no output" >&2; exit 1; }
date '+%Y-%m-%dT%H:%M:%S' > "${UNIT_DIR}/.done.tmp" && mv "${UNIT_DIR}/.done.tmp" "${UNIT_DIR}/.done"
echo "job: ${UNIT}: done"
