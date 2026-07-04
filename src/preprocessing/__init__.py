"""
preprocessing
=============

Sidecar generation (acqparams, index, slspec) for the dMRI preprocessing stage.
The external command orchestration (FSL / MRtrix / ANTs) lives in the shell
scripts under ``steps/``; this package only contains the parameterized,
testable Python logic.
"""

from .sidecars import (
    build_acqparams, write_acqparams,
    count_volumes, build_index, write_index,
    build_slspec, write_slspec,
)

__all__ = [
    "build_acqparams", "write_acqparams",
    "count_volumes", "build_index", "write_index",
    "build_slspec", "write_slspec",
]
