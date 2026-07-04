#!/usr/bin/env python
"""Generate the eddy slspec file from SliceTiming in a JSON sidecar.

Python port of ``slspec_writer.m``: it groups slices by acquisition time
(multiband groups) and writes 0-based indices.

Usage:
    python make_slspec.py --json <dwi.json> --out <slspec.txt>
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from preprocessing.sidecars import write_slspec  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", required=True, help="DWI JSON sidecar with SliceTiming")
    ap.add_argument("--out", required=True, help="output slspec .txt path")
    args = ap.parse_args()

    slspec = write_slspec(args.json, args.out)
    print(f"[slspec] {slspec.shape[0]} groups x {slspec.shape[1]} slices (MB) -> {args.out}")


if __name__ == "__main__":
    main()
