#!/usr/bin/env python
"""Batch preprocessing QC report: scan subjects, build a summary table (one row
per subject), and save it as CSV.

The script uses this preprocessing stage's naming convention to locate each
subject's eddy output. Adjust ``--basepath`` and ``--session`` for your setup.

Usage:
    python preprocessing_qc_report.py --basepath /path/to/data --out qc.csv
    python preprocessing_qc_report.py --basepath /path/to/data --subjects c01,c02 --out qc.csv
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from preprocessing_qc import cohort_qc_summary  # noqa: E402


def _one_match(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern))
    if len(matches) == 1:
        return matches[0]
    return None


def build_specs(basepath: Path, session: str, subjects: list[str]) -> list[dict]:
    """Build per-subject path specs using the repository naming convention."""
    specs = []
    for sub in subjects:
        dwidir = basepath / sub / session / "dwi"
        dendir = dwidir / "den"
        eddy_base = (dendir / "preproc-2" / "eddy-out"
                     / f"{sub}_{session}_dwi_den_grc_tec_preproc-2")
        raw_dwi = dwidir / f"{sub}_{session}_dwi.nii.gz"
        if not raw_dwi.exists():
            raw_dwi = _one_match(dwidir, "*_AP_*.nii.gz") or raw_dwi
        bval_path = raw_dwi.with_suffix("")
        if raw_dwi.name.endswith(".nii.gz"):
            bval_path = raw_dwi.with_name(raw_dwi.name[:-7] + ".bval")
        else:
            bval_path = raw_dwi.with_suffix(".bval")
        specs.append(dict(
            subject_id=sub,
            eddy_base=eddy_base,
            dwi_path=raw_dwi,
            noise_path=dendir / "denoising-der" / f"{sub}_{session}_dwi_noise.nii.gz",
            bval_path=bval_path,
        ))
    return specs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--basepath", required=True, type=Path, help="data root")
    ap.add_argument("--session", default="ses-T0", help="session label (default: ses-T0)")
    ap.add_argument("--subjects", default=None,
                    help="comma-separated list; defaults to all subdirectories")
    ap.add_argument("--out", default="preprocessing_qc_summary.csv", help="output CSV")
    args = ap.parse_args()

    if args.subjects:
        subjects = [s.strip() for s in args.subjects.split(",") if s.strip()]
    else:
        subjects = sorted(
            p.name for p in args.basepath.iterdir()
            if (p / args.session / "dwi").is_dir()
        )

    if not subjects:
        print(f"No subject directories were found in {args.basepath}")
        sys.exit(1)

    print(f"Subjects: {len(subjects)} -> {subjects}")
    summary = cohort_qc_summary(build_specs(args.basepath, args.session, subjects))
    summary.to_csv(args.out)
    print(f"[qc] summary for {len(summary)} subjects -> {args.out}")


if __name__ == "__main__":
    main()
