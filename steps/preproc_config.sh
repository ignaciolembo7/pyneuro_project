#!/bin/bash
# preproc_config.sh
# =================
# Common preprocessing configuration. This file is sourced by the dispatcher and
# by each step. Every value can be overridden with an environment variable, which
# removes the hardcoded absolute paths from the original scripts.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Data root. The pipeline expects one subject directory per entry.
: "${BASEPATH:=${REPO_ROOT}/data}"

# Session and parameters that were variables/constants in the original scripts.
: "${SESSION:=ses-T0}"
: "${BET_THR:=0.3}"                 # bet threshold (-f), original 0.3
: "${DENOISE_NTHREADS:=8}"          # dwidenoise -nthreads, original 8
: "${BIAS_NTHREADS:=16}"            # dwibiascorrect -nthreads, original 16
: "${TOPUP_CONFIG:=b02b0_1.cnf}"    # topup --config, original b02b0_1.cnf

# Optional FSL version switcher. The original script sourced
# `~/fsl6.0.3_switcher.sh`; here it is sourced only when present.
: "${FSL_SWITCHER:=$HOME/fsl6.0.3_switcher.sh}"

# Python sidecar scripts, resolved relative to this repository layout.
PREPROC_SCRIPTS_DIR="${REPO_ROOT}/scripts"

load_fsl() {
  if [ -f "${FSL_SWITCHER}" ]; then
    # shellcheck disable=SC1090
    . "${FSL_SWITCHER}"
  fi
  which fsl || true
}

require_file() {
  local path="$1"
  local label="$2"
  if [ ! -f "${path}" ]; then
    echo "Missing ${label}: ${path}" >&2
    exit 1
  fi
}

require_subject_layout() {
  local sub="$1"
  local dwidir="${BASEPATH}/${sub}/${SESSION}/dwi"
  if [ ! -d "${dwidir}" ]; then
    echo "Missing DWI directory for subject '${sub}': ${dwidir}" >&2
    echo "Expected layout: ${BASEPATH}/<subject>/${SESSION}/dwi" >&2
    exit 1
  fi
}

find_one_match() {
  local dir="$1"
  local pattern="$2"
  local label="$3"
  local matches=()

  shopt -s nullglob
  matches=("${dir}"/${pattern})
  shopt -u nullglob

  if [ "${#matches[@]}" -eq 0 ]; then
    echo "Missing ${label}: no '${pattern}' file in ${dir}" >&2
    exit 1
  fi
  if [ "${#matches[@]}" -gt 1 ]; then
    echo "Ambiguous ${label}: found ${#matches[@]} matches for '${pattern}' in ${dir}" >&2
    printf '  %s\n' "${matches[@]}" >&2
    exit 1
  fi
  printf '%s\n' "${matches[0]}"
}

resolve_dwi_nifti() {
  local sub="$1"
  local dwidir="${BASEPATH}/${sub}/${SESSION}/dwi"
  local canonical="${dwidir}/${sub}_${SESSION}_dwi.nii.gz"
  if [ -f "${canonical}" ]; then
    printf '%s\n' "${canonical}"
    return
  fi
  find_one_match "${dwidir}" "*_AP_*.nii.gz" "AP DWI NIfTI"
}

resolve_pa_nifti() {
  local sub="$1"
  local fmapdir="${BASEPATH}/${sub}/${SESSION}/fmap"
  local canonical="${fmapdir}/${sub}_${SESSION}_dwi_dirPA-b0.nii.gz"
  if [ -f "${canonical}" ]; then
    printf '%s\n' "${canonical}"
    return
  fi
  find_one_match "${fmapdir}" "*_PA_*.nii.gz" "PA topup NIfTI"
}

sidecar_for_nifti() {
  local nifti="$1"
  local ext="$2"
  printf '%s%s\n' "${nifti%.nii.gz}" "${ext}"
}
