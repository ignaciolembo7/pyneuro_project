#!/usr/bin/env python
"""Generate the acqparams file for topup/eddy from AP and PA JSON sidecars.

This replaces ``acqparams-generator.py`` by removing absolute paths: JSON
sidecars are passed as arguments and acqparams is written to the requested path.

Usage:
    python make_acqparams.py --ap-json <AP.json> --pa-json <PA.json> --out <acqparams.txt>
"""
import argparse
import sys
from pathlib import Path

# permitir importar el paquete desde src/ sin instalarlo
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from preprocessing.sidecars import write_acqparams  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ap-json", required=True, help="A>>P series JSON sidecar (dwi)")
    ap.add_argument("--pa-json", required=True, help="P>>A series JSON sidecar (fmap)")
    ap.add_argument("--out", required=True, help="output acqparams .txt path")
    args = ap.parse_args()

    data = write_acqparams(args.ap_json, args.pa_json, args.out)
    print(f"[acqparams] wrote {args.out}")
    print(data)


if __name__ == "__main__":
    main()
