#!/bin/bash
# run_preproc.sh
# ==============
# Preprocessing-stage dispatcher for brain acquisitions.
#
# Usage:
#   run_preproc.sh <step> [<step> ...] [--subjects s1,s2,...]
#
#   step   : den_gr | topup | eddy | bias   (any order; steps run in the
#            canonical scientific order den_gr -> topup -> eddy -> bias)
#
# Examples:
#   ./run_preproc.sh den_gr topup eddy bias
#   ./run_preproc.sh eddy --subjects c01,c02
#
# Without --subjects, all subject directories under BASEPATH are processed.
set -e

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=preproc_config.sh
source "${here}/preproc_config.sh"

[ $# -gt 0 ] || { echo "usage: run_preproc.sh <steps...> [--subjects s1,s2,...]"; exit 1; }

# Backward-compatible no-op for old commands that started with "brains".
if [ "${1}" = "brains" ]; then
  shift
fi

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

echo "dataset=brains | steps=${!want[*]} | subjects=${#subjects[@]}"
for sub in "${subjects[@]}"; do
  require_subject_layout "${sub}"
  echo "======================================================"
  echo "=== brains :: ${sub} ==="
  for step in "${order[@]}"; do
    [ -n "${want[$step]:-}" ] || continue
    bash "${here}/step_${step}.sh" "${sub}"
  done
done
echo "======================================================"
echo "Preprocessing finished."
