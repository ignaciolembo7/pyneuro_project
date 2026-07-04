"""
sidecars.py
===========

Generate the sidecars that FSL topup / eddy need from each subject's .json and
.nii.gz files:

- ``acqparams``  : phase-encoding direction + total readout time (topup/eddy).
- ``index``      : one index per volume pointing to the acqparams row (eddy).
- ``slspec``     : multiband slice grouping by acquisition time (eddy).

This module is the parameterized, testable Python version of the logic that was
previously split across ``acqparams-generator.py`` (Python), a bash loop with a
hardcoded number of volumes (181), and ``slspec_writer.m`` (MATLAB).

It does not change any scientific decision: it reproduces the same values while
removing absolute paths and fixed counts by deriving them from the data.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

try:
    import nibabel as nib
except ImportError:
    nib = None


# ===========================================================================
# ACQPARAMS  (parameterized replacement for acqparams-generator.py)
# ===========================================================================
def _read_pe_readout(json_path: str | Path) -> tuple[str, float]:
    """Read phase-encoding direction and total readout time from a JSON sidecar."""
    with open(json_path) as fh:
        meta = json.load(fh)
    return meta["PhaseEncodingDirection"], float(meta["TotalReadoutTime"])


def build_acqparams(ap_json: str | Path, pa_json: str | Path) -> np.ndarray:
    """Build the acqparams matrix (4 rows x 4 columns).

    This reproduces ``acqparams-generator.py``:
    A>>P (``j-``) -> ``[0, -1, 0, ROT]`` and P>>A (``j``) -> ``[0, 1, 0, ROT]``,
    stacked as ``(AP, AP, PA, PA)`` (two b=0 volumes per series).
    """
    ap_pe, ap_rot = _read_pe_readout(ap_json)
    pa_pe, pa_rot = _read_pe_readout(pa_json)

    if ap_pe != "j-":
        raise ValueError(f"The expected A>>P series is not 'j-' (found '{ap_pe}').")
    if pa_pe != "j":
        raise ValueError(f"The expected P>>A series is not 'j' (found '{pa_pe}').")
    if ap_rot != pa_rot:
        # The original script only warned, so keep that behavior.
        import warnings
        warnings.warn("TotalReadoutTime differs between A>>P and P>>A.", stacklevel=2)

    ap_vec = np.array([0, -1, 0, ap_rot])
    pa_vec = np.array([0, 1, 0, pa_rot])
    return np.vstack((ap_vec, ap_vec, pa_vec, pa_vec))


def write_acqparams(ap_json, pa_json, out_path) -> np.ndarray:
    """Write acqparams using the original format (``%i %i %i %.6f``)."""
    data = build_acqparams(ap_json, pa_json)
    fmt = ["%i", "%i", "%i", "%.6f"]
    with open(out_path, "w") as fh:
        np.savetxt(fh, data, fmt=fmt, delimiter=" ")
    return data


# ===========================================================================
# INDEX  (replaces the bash loop with hardcoded 181 -> derive from data)
# ===========================================================================
def count_volumes(nifti_path: str | Path) -> int:
    """Return the number of volumes (dim4) by reading only the NIfTI header."""
    if nib is None:
        raise ImportError("nibabel is required to count volumes.")
    shape = nib.load(str(nifti_path)).header.get_data_shape()
    return int(shape[3]) if len(shape) == 4 else 1


def build_index(n_volumes: int, row: int = 1) -> np.ndarray:
    """Build an eddy index vector: one ``row`` per volume.

    All volumes point to the same acqparams row, matching the original script.
    """
    if n_volumes < 1:
        raise ValueError("n_volumes must be >= 1.")
    return np.full(n_volumes, row, dtype=int)


def write_index(nifti_path, out_path, row: int = 1) -> int:
    """Derive the number of volumes from the NIfTI and write one-line index."""
    n = count_volumes(nifti_path)
    idx = build_index(n, row=row)
    with open(out_path, "w") as fh:
        fh.write(" ".join(str(v) for v in idx) + "\n")
    return n


# ===========================================================================
# SLSPEC  (Python port of slspec_writer.m)
# ===========================================================================
def _read_slice_timing(json_path: str | Path) -> np.ndarray:
    with open(json_path) as fh:
        meta = json.load(fh)
    return np.asarray(meta["SliceTiming"], dtype=float)


def build_slspec(slice_times) -> np.ndarray:
    """Build slspec (multiband slice groups) from slice timings.

    Each row contains slices excited simultaneously (same time), ordered by
    acquisition time. Indices are 0-based, as expected by eddy.
    """
    slice_times = np.asarray(slice_times, dtype=float)
    order = np.argsort(slice_times, kind="stable")      # sindx (0-based)
    sorted_t = slice_times[order]
    n_groups = int(np.sum(np.diff(sorted_t) != 0) + 1)   # distinct time groups
    n = order.size
    if n % n_groups != 0:
        raise ValueError("The number of slices is not a multiple of the number of "
                         "time groups; check SliceTiming.")
    mb = n // n_groups                                   # multiband factor
    # Column-major reshape (MATLAB-style) [mb, n_groups], then transpose.
    return order.reshape((mb, n_groups), order="F").T


def write_slspec(json_path, out_path) -> np.ndarray:
    """Generate slspec from the JSON sidecar and write space-separated integers."""
    slspec = build_slspec(_read_slice_timing(json_path))
    np.savetxt(out_path, slspec, fmt="%d", delimiter=" ")
    return slspec
