#!/bin/bash
# step_den_gr.sh
# ==============
# Denoising (MP-PCA) + Gibbs ringing correction with MRtrix.
# Faithful to 1_denoising_gibbs-ringing.sh (same commands and flags).
set -e

sub="${1:?usage: step_den_gr.sh <sub>}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=preproc_config.sh
source "${here}/preproc_config.sh"

dwidir="${BASEPATH}/${sub}/${SESSION}/dwi"
dendir="${dwidir}/den"
mkdir -p "${dendir}/denoising-der"

dwiin="$(resolve_dwi_nifti "${sub}")"
dwiout="${dendir}/${sub}_${SESSION}_dwi_den.nii.gz"
noise="${dendir}/denoising-der/${sub}_${SESSION}_dwi_noise.nii.gz"
residuals="${dendir}/denoising-der/${sub}_${SESSION}_dwi_den-residuals.nii.gz"
dwioutgrc="${dendir}/${sub}_${SESSION}_dwi_den_grc.nii.gz"

require_file "${dwiin}" "input DWI"

# ---------------- original commands (unchanged) ----------------
dwidenoise -force -nthreads "${DENOISE_NTHREADS}" -noise "${noise}" "${dwiin}" "${dwiout}"
mrcalc -force "${dwiin}" "${dwiout}" -subtract "${residuals}"
mrdegibbs -force "${dwiout}" "${dwioutgrc}"
# -------------------------------------------------------------------

echo "den_gr OK: ${sub}"
