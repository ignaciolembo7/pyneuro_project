#!/bin/bash
# step_eddy.sh
# ============
# Eddy-current and motion correction with FSL eddy + QC (eddy_quad).
# Faithful to 3_preproc-2_eddy.sh (same commands and flags).
# Allowed changes (parameterization only):
#   - the index is derived from the number of volumes (previously hardcoded as 181),
#   - slspec is generated with make_slspec.py (port of slspec_writer.m).
set -e

sub="${1:?usage: step_eddy.sh <sub>}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=preproc_config.sh
source "${here}/preproc_config.sh"

load_fsl
thr="${BET_THR}"

if [ -n "${EDDY_CMD:-}" ]; then
  if ! command -v "${EDDY_CMD}" >/dev/null 2>&1; then
    echo "Requested EDDY_CMD not found in PATH: ${EDDY_CMD}" >&2
    exit 1
  fi
else
  for candidate in eddy_openmp eddy_cpu eddy; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      EDDY_CMD="${candidate}"
      break
    fi
  done
  if [ -z "${EDDY_CMD:-}" ]; then
    echo "Missing FSL eddy executable: tried eddy_openmp, eddy_cpu, eddy" >&2
    exit 1
  fi
fi

dwidir="${BASEPATH}/${sub}/${SESSION}/dwi"
dendir="${dwidir}/den"
mkdir -p "${dendir}/preproc-2/eddy-in" "${dendir}/preproc-2/eddy-out"

raw_dwi="$(resolve_dwi_nifti "${sub}")"
myimain="${dendir}/${sub}_${SESSION}_dwi_den_grc.nii.gz"
myacqp="${dendir}/preproc-1/topup-in/${sub}_acqparam_b0s-all.txt"
mybvecs="$(sidecar_for_nifti "${raw_dwi}" ".bvec")"
mybvals="$(sidecar_for_nifti "${raw_dwi}" ".bval")"
myjson="$(sidecar_for_nifti "${raw_dwi}" ".json")"
mytopup="${dendir}/preproc-1/topup-out/${sub}_${SESSION}_dwi_topup-out-preproc-1"
myout="${dendir}/preproc-2/eddy-out/${sub}_${SESSION}_dwi_den_grc_tec_preproc-2"
mymask="${dendir}/preproc-1/topup-out/${sub}_${SESSION}_dwi_topup-out-preproc-1-unwarp-imgs-mean_brain-f${thr}R_mask.nii.gz"

# index: derive the number of volumes (replaces the hardcoded 181).
findex="${dendir}/preproc-2/eddy-in/${sub}_${SESSION}_dwi_preproc-2-index.txt"
mkdir -p "$(dirname "${findex}")"

require_file "${myimain}" "denoised and Gibbs-corrected DWI"
require_file "${myacqp}" "acqparams file"
require_file "${mybvecs}" "bvec file"
require_file "${mybvals}" "bval file"
require_file "${mytopup}_fieldcoef.nii.gz" "topup field coefficients"
require_file "${mymask}" "brain mask"
require_file "${myjson}" "DWI JSON sidecar"

python "${PREPROC_SCRIPTS_DIR}/make_index.py" --dwi "${myimain}" --out "${findex}"

# slspec: generate from the JSON sidecar (port of slspec_writer.m)
myslspec="${dendir}/preproc-2/eddy-in/${sub}_my_slspec.txt"
python "${PREPROC_SCRIPTS_DIR}/make_slspec.py" --json "${myjson}" --out "${myslspec}"

# ---------------- original commands (unchanged) ----------------
"${EDDY_CMD}" --imain=${myimain} --mask=${mymask} --acqp=${myacqp} --index=${findex} \
  --bvecs=${mybvecs} --bvals=${mybvals} --topup=${mytopup} --out=${myout} \
  --repol --ol_type=both --slspec=${myslspec} --cnr_maps --residuals ${EDDY_EXTRA_ARGS:-}

cd "${dendir}/preproc-2/eddy-out"
eddy_quad ${myout} -idx ${findex} -par ${myacqp} -m ${mymask} -b ${mybvals} -s ${myslspec}
# -------------------------------------------------------------------

mkdir -p "${dendir}/preproc-2/bias-corr"
echo "eddy OK: ${sub}"
