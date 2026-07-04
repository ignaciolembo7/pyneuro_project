#!/bin/bash
# run_preproc.sh
# ==============
# Preprocessing-stage dispatcher using the same cohort + token style as the
# larger pipeline.
#
# Usage:
#   run_preproc.sh <cohort> <step> [<step> ...] [--subjects s1,s2,...]
#
#   cohort : brains | phantoms
#   step   : den_gr | topup | eddy | bias   (any order; steps run in the
#            canonical scientific order den_gr -> topup -> eddy -> bias)
#
# Examples:
#   ./run_preproc.sh brains den_gr topup eddy bias
#   ./run_preproc.sh phantoms den_gr eddy bias         # topup is skipped
#   ./run_preproc.sh brains eddy --subjects c01,c02
#
# Without --subjects, all subject directories under BASEPATH are processed.
set -e

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=preproc_config.sh
source "${here}/preproc_config.sh"

cohort="${1:?usage: run_preproc.sh <brains|phantoms> <steps...>}"; shift
case "${cohort}" in
  brains|phantoms) ;;
  *) echo "Invalid cohort: '${cohort}' (use brains or phantoms)"; exit 1;;
esac

# --- split steps from --subjects ---
declare -A want
subjects_csv=""
while [ $# -gt 0 ]; do
  case "$1" in
    --subjects) subjects_csv="$2"; shift 2;;
    den_gr|topup|eddy|bias) want["$1"]=1; shift;;
    *) echo "Unknown step: '$1' (use den_gr, topup, eddy, bias)"; exit 1;;
  esac
done
[ ${#want[@]} -gt 0 ] || { echo "No steps were provided"; exit 1; }

if [ "${cohort}" = "phantoms" ] && { [ -n "${want[eddy]:-}" ] || [ -n "${want[bias]:-}" ]; }; then
  echo "The current eddy/bias steps require topup-derived acqparams and masks." >&2
  echo "For phantoms, only den_gr is currently runnable in this repository layout." >&2
  exit 1
fi

# --- subject list ---
if [ -n "${subjects_csv}" ]; then
  IFS=',' read -r -a subjects <<< "${subjects_csv}"
else
  subjects=()
  for d in "${BASEPATH}"/*/; do
    [ -d "${d}/${SESSION}/dwi" ] && subjects+=("$(basename "$d")")
  done
fi
[ ${#subjects[@]} -gt 0 ] || {
  echo "No subject directories were found in ${BASEPATH}" >&2
  echo "Expected layout: ${BASEPATH}/<subject>/${SESSION}/dwi" >&2
  exit 1
}

# --- execution: canonical scientific order ---
order=(den_gr topup eddy bias)
export COHORT="${cohort}"

echo "cohort=${cohort} | steps=${!want[*]} | subjects=${#subjects[@]}"
for sub in "${subjects[@]}"; do
  require_subject_layout "${sub}"
  echo "======================================================"
  echo "=== ${cohort} :: ${sub} ==="
  for step in "${order[@]}"; do
    [ -n "${want[$step]:-}" ] || continue
    if [ "${step}" = "topup" ] && [ "${cohort}" = "phantoms" ]; then
      echo "topup: skipped for phantoms (2D, no reverse phase-encoding pair) - ${sub}"
      continue
    fi
    bash "${here}/step_${step}.sh" "${sub}"
  done
done
echo "======================================================"
echo "Preprocessing finished."
