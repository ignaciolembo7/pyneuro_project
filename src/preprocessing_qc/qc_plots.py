"""
qc_plots.py
===========

Quality-control (QC) visualizations for dMRI preprocessing.

This complements ``qc_metrics.py``: while that module produces tables
(``pandas``), this one produces figures (``matplotlib``) from the same pipeline
outputs. All functions return ``(fig, ax)`` so they can be displayed in a
notebook or saved with ``fig.savefig(...)``.

Dependencies: numpy, matplotlib. ``nibabel`` is only required for functions that
load NIfTI images (before/after comparisons).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

try:
    import nibabel as nib
except ImportError:
    nib = None


def _require_nibabel():
    if nib is None:
        raise ImportError("nibabel is required to plot NIfTI slices.")


def _load_volume(path, volume: int = 0):
    """Load a NIfTI image and return a 3D volume (select ``volume`` if 4D)."""
    _require_nibabel()
    data = nib.load(str(path)).get_fdata()
    if data.ndim == 4:
        volume = int(np.clip(volume, 0, data.shape[3] - 1))
        data = data[..., volume]
    return data


# ===========================================================================
# 1. BEFORE / AFTER SLICE COMPARISON
# ===========================================================================
def plot_before_after_slice(before_path, after_path, *, z=None, volume: int = 0,
                            titles=("Before", "After"), cmap: str = "gray",
                            show_diff: bool = True):
    """Compare one axial slice from two images.

    Examples include raw vs. denoised or den_grc vs. eddy-corrected. When
    ``show_diff`` is True, a third difference panel is added to show what the
    step removed (noise, ringing, distortion).
    """
    before = _load_volume(before_path, volume)
    after = _load_volume(after_path, volume)
    if z is None:
        z = before.shape[2] // 2

    b, a = before[:, :, z].T, after[:, :, z].T
    panels = [(b, titles[0]), (a, titles[1])]
    if show_diff:
        panels.append((a - b, "Difference"))

    fig, axes = plt.subplots(1, len(panels), figsize=(4.2 * len(panels), 4.4))
    axes = np.atleast_1d(axes)
    vmax = np.nanpercentile(np.concatenate([b.ravel(), a.ravel()]), 99)
    for ax, (img, title) in zip(axes, panels):
        if title == "Difference":
            lim = np.nanpercentile(np.abs(img), 99) or 1.0
            ax.imshow(img, cmap="RdBu_r", origin="lower", vmin=-lim, vmax=lim)
        else:
            ax.imshow(img, cmap=cmap, origin="lower", vmin=0, vmax=vmax)
        ax.set_title(title)
        ax.axis("off")
    fig.suptitle(f"Slice z={z}, volume={volume}", y=1.02)
    fig.tight_layout()
    return fig, axes


# ===========================================================================
# 2. MOTION ACROSS VOLUMES
# ===========================================================================
def plot_movement_rms(mrms_df, ax=None):
    """Plot absolute and relative motion RMS (from ``eddy``) by volume."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 3.6))
    else:
        fig = ax.figure
    ax.plot(mrms_df.index, mrms_df["abs_mm"], label="absolute", lw=1.5)
    ax.plot(mrms_df.index, mrms_df["rel_mm"], label="relative", lw=1.2)
    ax.set_xlabel("volume")
    ax.set_ylabel("motion RMS (mm)")
    ax.set_title("Motion estimated by eddy")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig, ax


def plot_motion_parameters(motion_df):
    """Two panels: translations (mm) and rotations (rad) by volume."""
    fig, axes = plt.subplots(2, 1, figsize=(8, 5.5), sharex=True)
    for col in ["trans_x_mm", "trans_y_mm", "trans_z_mm"]:
        axes[0].plot(motion_df.index, motion_df[col], lw=1.2, label=col.split("_")[1])
    axes[0].set_ylabel("translation (mm)")
    axes[0].legend(frameon=False, ncol=3)
    axes[0].grid(alpha=0.25)
    for col in ["rot_x_rad", "rot_y_rad", "rot_z_rad"]:
        axes[1].plot(motion_df.index, motion_df[col], lw=1.2, label=col.split("_")[1])
    axes[1].set_ylabel("rotation (rad)")
    axes[1].set_xlabel("volume")
    axes[1].legend(frameon=False, ncol=3)
    axes[1].grid(alpha=0.25)
    fig.suptitle("Motion parameters (eddy_parameters)")
    fig.tight_layout()
    return fig, axes


# ===========================================================================
# 3. OUTLIER MAP (slices x volumes)
# ===========================================================================
def plot_outlier_heatmap(outlier_map, ax=None):
    """Heatmap of slices marked as outliers: rows = slices, cols = volumes."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 3.8))
    else:
        fig = ax.figure
    # Transpose so the x-axis is volumes.
    im = ax.imshow(outlier_map.T.values, aspect="auto", cmap="Reds",
                   interpolation="nearest", origin="lower")
    ax.set_xlabel("volume")
    ax.set_ylabel("slice")
    ax.set_title("Slices detected as outliers (--repol)")
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label="outlier (0/1)")
    fig.tight_layout()
    return fig, ax


# ===========================================================================
# 4. SHELLS AND CNR
# ===========================================================================
def plot_shells(shells_df, ax=None):
    """Bar plot with the number of directions per shell (b-value)."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 3.6))
    else:
        fig = ax.figure
    labels = [f"b={int(b)}" for b in shells_df["b_value"]]
    ax.bar(labels, shells_df["n_directions"], color="#3a7ca5")
    ax.set_ylabel("number of directions")
    ax.set_title("Acquisition scheme (shells)")
    for i, v in enumerate(shells_df["n_directions"]):
        ax.text(i, v, str(int(v)), ha="center", va="bottom", fontsize=9)
    ax.grid(alpha=0.2, axis="y")
    fig.tight_layout()
    return fig, ax


def plot_cnr_per_shell(qc_json, ax=None):
    """Bar plot of average CNR per shell from eddy_quad ``qc.json``.

    In eddy_quad, the first value in ``qc_cnr_avg`` is usually b=0 SNR and the
    rest are CNR values for each diffusion shell.
    """
    cnr = qc_json.get("qc_cnr_avg")
    if not cnr:
        raise ValueError("qc.json does not contain 'qc_cnr_avg'.")
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 3.6))
    else:
        fig = ax.figure
    labels = ["b0 (SNR)"] + [f"shell {i}" for i in range(1, len(cnr))]
    ax.bar(labels, cnr, color="#8a5a44")
    ax.set_ylabel("CNR / SNR")
    ax.set_title("CNR by shell (eddy_quad)")
    ax.grid(alpha=0.2, axis="y")
    fig.tight_layout()
    return fig, ax


# ===========================================================================
# 5. BETWEEN-SUBJECT COMPARISON (from the cohort table)
# ===========================================================================
def plot_cohort_metric(summary_df, column: str, ax=None, ylabel=None):
    """Bar plot for one metric from the cohort summary, one subject per bar.

    Useful for spotting atypical subjects at a glance (high motion, many
    outliers, low SNR, etc.).
    """
    if column not in summary_df.columns:
        raise KeyError(f"'{column}' is not in the summary. "
                       f"Columns: {list(summary_df.columns)}")
    if ax is None:
        fig, ax = plt.subplots(figsize=(max(5, 0.7 * len(summary_df)), 3.6))
    else:
        fig = ax.figure
    ax.bar(summary_df.index.astype(str), summary_df[column], color="#4c9a76")
    ax.set_ylabel(ylabel or column)
    ax.set_title(f"{column} by subject")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.2, axis="y")
    fig.tight_layout()
    return fig, ax
