#!/usr/bin/env python
"""Generate the eddy index file by deriving the number of DWI volumes.

This replaces the bash loop with the hardcoded number of volumes (181): it reads
image dim4 and writes one index per volume (all = 1, matching the original).

Usage:
    python make_index.py --dwi <dwi.nii.gz> --out <index.txt>
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from preprocessing.sidecars import write_index  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dwi", required=True, help="input DWI used to count volumes")
    ap.add_argument("--out", required=True, help="output index .txt path")
    ap.add_argument("--row", type=int, default=1,
                    help="acqparams row pointed to by each volume (default: 1)")
    args = ap.parse_args()

    n = write_index(args.dwi, args.out, row=args.row)
    print(f"[index] {n} volumes -> {args.out}")


if __name__ == "__main__":
    main()
