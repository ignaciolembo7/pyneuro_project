"""Tests for the sidecar generators (acqparams, index, slspec).

They verify that the Python version reproduces the original script logic
(acqparams-generator.py and slspec_writer.m).

Run with: pytest -q
"""
import json

import numpy as np
import pytest

from preprocessing.sidecars import (
    build_acqparams, write_acqparams, build_index, build_slspec,
)


def _write_json(path, meta):
    with open(path, "w") as fh:
        json.dump(meta, fh)


# ---------------------------------------------------------------- acqparams
def test_acqparams_reproduce_c01(tmp_path):
    """It must match the acqparams from output.txt (subject c01)."""
    ap = tmp_path / "ap.json"
    pa = tmp_path / "pa.json"
    _write_json(ap, {"PhaseEncodingDirection": "j-", "TotalReadoutTime": 0.0333199})
    _write_json(pa, {"PhaseEncodingDirection": "j", "TotalReadoutTime": 0.0333199})

    data = build_acqparams(ap, pa)
    expected = np.array([[0, -1, 0, 0.0333199]] * 2 + [[0, 1, 0, 0.0333199]] * 2)
    assert np.allclose(data, expected)


def test_acqparams_written_format(tmp_path):
    ap = tmp_path / "ap.json"
    pa = tmp_path / "pa.json"
    _write_json(ap, {"PhaseEncodingDirection": "j-", "TotalReadoutTime": 0.0333199})
    _write_json(pa, {"PhaseEncodingDirection": "j", "TotalReadoutTime": 0.0333199})
    out = tmp_path / "acq.txt"
    write_acqparams(ap, pa, out)
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 4
    assert lines[0].split() == ["0", "-1", "0", "0.033320"]


def test_acqparams_rejects_wrong_pe(tmp_path):
    ap = tmp_path / "ap.json"
    pa = tmp_path / "pa.json"
    _write_json(ap, {"PhaseEncodingDirection": "j", "TotalReadoutTime": 0.03})   # wrong
    _write_json(pa, {"PhaseEncodingDirection": "j", "TotalReadoutTime": 0.03})
    with pytest.raises(ValueError):
        build_acqparams(ap, pa)


# -------------------------------------------------------------------- index
def test_index_length():
    assert build_index(181).tolist() == [1] * 181


def test_index_custom_row():
    assert build_index(3, row=2).tolist() == [2, 2, 2]


def test_index_invalid():
    with pytest.raises(ValueError):
        build_index(0)


# ------------------------------------------------------------------- slspec
def test_slspec_multiband():
    """MB=2, 6 slices, 3 temporal groups -> expected grouping."""
    times = [0, 0.2, 0.4, 0, 0.2, 0.4]  # slices 0..5
    slspec = build_slspec(times)
    assert slspec.tolist() == [[0, 3], [1, 4], [2, 5]]


def test_slspec_single_band():
    times = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
    slspec = build_slspec(times)
    assert slspec.shape == (6, 1)
    assert slspec.ravel().tolist() == [0, 1, 2, 3, 4, 5]
