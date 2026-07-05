#!/bin/bash
# step_bias.sh
# ============
# B1 bias-field correction with MRtrix + ANTs (dwibiascorrect ants).
# Faithful to 4_preproc-2_bias-corr.sh (same commands and flags).
set -e

sub="${1:?usage: step_bias.sh <sub>}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=preproc_config.sh
source "${here}/preproc_config.sh"

thr="${BET_THR}"
dwidir="${BASEPATH}/${sub}/${SESSION}/dwi"
dendir="${dwidir}/den"
mkdir -p "${dendir}/preproc-2/bias-corr"

raw_dwi="$(resolve_dwi_nifti "${sub}")"
dwiin="${dendir}/preproc-2/eddy-out/${sub}_${SESSION}_dwi_den_grc_tec_preproc-2.nii.gz"
dwiout="${dendir}/preproc-2/bias-corr/${sub}_${SESSION}_dwi_den_grc_tec_preproc-2_bias-corr.nii.gz"
biasfield="${dendir}/preproc-2/bias-corr/${sub}_${SESSION}_dwi_den_grc_tec_preproc-2_bias-field.nii.gz"
mymask="${dendir}/preproc-1/topup-out/${sub}_${SESSION}_dwi_topup-out-preproc-1-unwarp-imgs-mean_brain-f${thr}R_mask.nii.gz"
inbvecs="${dendir}/preproc-2/eddy-out/${sub}_${SESSION}_dwi_den_grc_tec_preproc-2.eddy_rotated_bvecs"
inbvals="$(sidecar_for_nifti "${raw_dwi}" ".bval")"

require_file "${dwiin}" "eddy-corrected DWI"
require_file "${mymask}" "brain mask"
require_file "${inbvecs}" "eddy-rotated bvecs"
require_file "${inbvals}" "bval file"

# ---------------- original command (unchanged) ----------------
dwibiascorrect ants -fslgrad "${inbvecs}" "${inbvals}" -mask "${mymask}" \
  -force -bias "${biasfield}" -nthreads "${BIAS_NTHREADS}" "${dwiin}" "${dwiout}"
# ----------------------------------------------------------------

echo "bias OK: ${sub}"
