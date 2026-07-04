"""Tests for QC metrics that do not require NIfTI images.

Run with: pytest -q
"""
import json

import numpy as np
import pandas as pd

from preprocessing_qc import (
    load_movement_rms, load_outlier_map, summarize_outliers,
    load_qc_json, qc_json_to_series, summarize_shells,
    subject_qc_summary, cohort_qc_summary,
)


# ------------------------------------------------------------- useful fixtures
def _make_eddy_outputs(base, nvol=20, nsl=10, seed=0):
    """Create minimal synthetic FSL eddy/eddy_quad-like outputs on disk."""
    rng = np.random.default_rng(seed)
    mrms = np.abs(rng.normal(0.3, 0.1, size=(nvol, 2)))
    np.savetxt(str(base) + ".eddy_movement_rms", mrms)

    omap = (rng.random((nvol, nsl)) < 0.05).astype(int)
    with open(str(base) + ".eddy_outlier_map", "w") as fh:
        fh.write("header line\n")
        np.savetxt(fh, omap, fmt="%d")

    qcdir = base.parent / (base.name + ".qc")
    qcdir.mkdir(exist_ok=True)
    json.dump({"qc_mot_abs": 0.3, "qc_mot_rel": 0.14, "qc_outliers_tot": 1.2,
               "data_no_shells": 4, "qc_cnr_avg": [18.0, 6.5, 8.1, 12.9]},
              open(qcdir / "qc.json", "w"))
    return omap


# ------------------------------------------------------------------ tests
def test_movement_rms_columns(tmp_path):
    base = tmp_path / "sub"
    _make_eddy_outputs(base)
    df = load_movement_rms(str(base) + ".eddy_movement_rms")
    assert list(df.columns) == ["abs_mm", "rel_mm"]
    assert df.index.name == "volume"


def test_outlier_summary(tmp_path):
    base = tmp_path / "sub"
    omap = _make_eddy_outputs(base)
    df = load_outlier_map(str(base) + ".eddy_outlier_map")
    s = summarize_outliers(df)
    assert int(s["outlier_slices_total"]) == int(omap.sum())
    assert 0 <= s["outlier_slices_pct"] <= 100


def test_qc_json_series(tmp_path):
    base = tmp_path / "sub"
    _make_eddy_outputs(base)
    qc = load_qc_json(str(base) + ".qc/qc.json")
    s = qc_json_to_series(qc)
    assert s["n_shells"] == 4
    assert "cnr_avg" in s and "cnr_shell0" in s


def test_shells_summary(tmp_path):
    bval = tmp_path / "x.bval"
    bvals = np.concatenate([np.zeros(21), np.full(32, 700), np.full(64, 1000)])
    np.savetxt(bval, bvals[None, :], fmt="%d")
    df = summarize_shells(bval)
    assert df.loc[df.b_value == 0, "n_directions"].item() == 21
    assert df.loc[df.b_value == 700, "n_directions"].item() == 32


def test_subject_and_cohort_summary(tmp_path):
    base = tmp_path / "c01_sub"
    _make_eddy_outputs(base)
    one = subject_qc_summary("c01", base)
    assert one.index.tolist() == ["c01"]
    assert "mot_abs_mm_mean" in one.columns

    coh = cohort_qc_summary([
        {"subject_id": "c01", "eddy_base": base},
        {"subject_id": "c02", "eddy_base": base},
    ])
    assert coh.shape[0] == 2
