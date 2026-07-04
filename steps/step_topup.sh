#!/bin/bash
# step_topup.sh
# =============
# Susceptibility distortion correction with FSL topup. BRAINS ONLY.
# Faithful to 2_preproc-1_topup.sh (same commands and flags).
# acqparams is generated with make_acqparams.py (same content as the original).
set -e

sub="${1:?usage: step_topup.sh <sub>}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=preproc_config.sh
source "${here}/preproc_config.sh"

# Guard against direct phantom calls; the dispatcher already skips this step.
if [ "${COHORT:-brains}" = "phantoms" ]; then
  echo "topup: skipped for phantoms (2D, no reverse phase-encoding pair) - ${sub}"
  exit 0
fi

load_fsl

dwidir="${BASEPATH}/${sub}/${SESSION}/dwi"
fmapdir="${BASEPATH}/${sub}/${SESSION}/fmap"
dendir="${dwidir}/den"
mkdir -p "${dendir}/preproc-1/topup-in" "${dendir}/preproc-1/topup-out"
topupin="${dendir}/preproc-1/topup-in"
topupout="${dendir}/preproc-1/topup-out"

dwiser="$(resolve_dwi_nifti "${sub}")"
PAser="$(resolve_pa_nifti "${sub}")"
ap_json="$(sidecar_for_nifti "${dwiser}" ".json")"
pa_json="$(sidecar_for_nifti "${PAser}" ".json")"
b0sAP="${topupin}/${sub}_${SESSION}_dwi_2-b0-AP-raw.nii.gz"
b0sPA="${topupin}/${sub}_${SESSION}_dwi_2-b0-PA-raw.nii.gz"

require_file "${dwiser}" "AP DWI"
require_file "${PAser}" "PA b0 fieldmap"
require_file "${ap_json}" "AP DWI JSON sidecar"
require_file "${pa_json}" "PA b0 JSON sidecar"

# ---------------- original commands (unchanged) ----------------
fslselectvols -i "${dwiser}" -o "${b0sAP}" --vols=0,1
fslselectvols -i "${PAser}" -o "${b0sPA}" --vols=3,4

b0sall="${topupin}/${sub}_${SESSION}_dwi_b0s-all-4topup.nii.gz"
fslmerge -t "${b0sall}" "${b0sAP}" "${b0sPA}"

# acqparams desde los .json (refactor Python de acqparams-generator.py)
acqparams="${topupin}/${sub}_acqparam_b0s-all.txt"
python "${PREPROC_SCRIPTS_DIR}/make_acqparams.py" \
  --ap-json "${ap_json}" \
  --pa-json "${pa_json}" \
  --out "${acqparams}"

topup --imain="${b0sall}" --datain="${acqparams}" --config=${TOPUP_CONFIG} \
  --out="${topupout}/${sub}_${SESSION}_dwi_topup-out-preproc-1" \
  --fout="${topupout}/${sub}_${SESSION}_dwi_topup-out-preproc-1-field" \
  --iout="${topupout}/${sub}_${SESSION}_dwi_topup-out-preproc-1-unwarp-imgs" \
  --logout="${topupout}/${sub}_${SESSION}_dwi_topup-out-preproc-1-log"

fslmaths "${topupout}/${sub}_${SESSION}_dwi_topup-out-preproc-1-unwarp-imgs.nii.gz" \
  -Tmean "${topupout}/${sub}_${SESSION}_dwi_topup-out-preproc-1-unwarp-imgs-mean.nii.gz"

bet "${topupout}/${sub}_${SESSION}_dwi_topup-out-preproc-1-unwarp-imgs-mean.nii.gz" \
  "${topupout}/${sub}_${SESSION}_dwi_topup-out-preproc-1-unwarp-imgs-mean_brain-f${BET_THR}R.nii.gz" \
  -f ${BET_THR} -R -m
# -------------------------------------------------------------------

echo "topup OK: ${sub}"
