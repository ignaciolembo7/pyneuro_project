# nogse-preproc

dMRI preprocessing and quality-control (QC) tools for OGSE/NOGSE acquisitions.
The repository wraps the original FSL / MRtrix3 / ANTs preprocessing commands in
small selectable shell steps, and keeps the analysis/QC layer in Python
(`pandas` + `matplotlib`).

## Repository Layout

```text
nogse-preproc/
├── README.md
├── requirements.txt
├── pyproject.toml
├── data/                           # expected data root, one subject directory per entry
├── notebooks/
│   └── preprocessing_qc_demo.ipynb
├── scripts/                        # Python CLI entry points
│   ├── make_acqparams.py
│   ├── make_index.py
│   ├── make_slspec.py
│   └── preprocessing_qc_report.py
├── src/
│   ├── preprocessing/              # sidecar generation logic
│   └── preprocessing_qc/           # QC metrics and plots
├── steps/                          # shell preprocessing pipeline
│   ├── preproc_config.sh
│   ├── run_preproc.sh
│   ├── step_den_gr.sh
│   ├── step_topup.sh
│   ├── step_eddy.sh
│   └── step_bias.sh
└── tests/
    ├── test_sidecars.py
    └── test_qc_metrics.py
```

The current repository layout is flat at the top level: shell steps live in
`steps/`, Python command-line scripts live in `scripts/`, and importable Python
packages live in `src/`.

## Expected Data Layout

By default, `steps/preproc_config.sh` sets `BASEPATH` to this repository's
`data/` directory. The preprocessing pipeline expects `data/` to contain one
directory per logical acquisition/subject, with this BIDS-like layout:

```text
data/
└── <subject>/
    └── ses-T0/
        ├── dwi/
        │   ├── *_AP_*.nii.gz
        │   ├── *_AP_*.json
        │   ├── *_AP_*.bvec
        │   └── *_AP_*.bval
        └── fmap/
            ├── *_PA_*.nii.gz
            └── *_PA_*.json
```

The NIfTI filenames do not need to be renamed. If a canonical
`<subject>_ses-T0_dwi.nii.gz` file exists, it is used; otherwise the shell steps
discover exactly one `*_AP_*.nii.gz` in `dwi/` and exactly one `*_PA_*.nii.gz` in
`fmap/`. Sidecars are expected to use the same original basename as the NIfTI.

The bundled data are organized as one logical acquisition per AP series:

```text
data/
├── _common/ses-T0/fmap/            # shared PA image for topup
├── brain3_hz000_d55_b2000/ses-T0/
├── brain3_hz015_d66p7_b3210/ses-T0/
├── brain3_hz020_d55_b1770/ses-T0/
├── brain3_hz040_d55_b0505/ses-T0/
└── brain3_hz055_d55_b0275/ses-T0/
```

Each acquisition has its original AP NIfTI under `dwi/` and a symlink to the
shared PA NIfTI under `fmap/`. The repository currently only includes NIfTI
images. `topup` still needs matching AP/PA JSON files with phase-encoding and
readout metadata, and `eddy` needs AP `.bvec` and `.bval` files. The scripts now
report missing sidecars explicitly before reaching FSL.

## Installation

Create and activate a conda environment from the repository root:

```bash
conda create -n pyneuro-preproc python=3.10
conda activate pyneuro-preproc
pip install -e .
```

If you also want the notebook and test dependencies, install the requirements
file:

```bash
pip install -r requirements.txt
```

External tools are installed separately and must be available on `PATH`:
FSL >= 6.0.3, MRtrix3 >= 3.0.2, and ANTs.

## Preprocessing Usage

Run from the repository root:

```bash
./steps/run_preproc.sh den_gr topup eddy bias
./steps/run_preproc.sh eddy --subjects c01,c02
```

Or point the pipeline to another data root:

```bash
export BASEPATH=/path/to/data
./steps/run_preproc.sh den_gr topup eddy bias
```

Steps are always executed in the canonical order `den_gr -> topup -> eddy ->
bias`, regardless of the order passed on the command line.

The preprocessing path is brain-only and supports the full chain (`den_gr`,
`topup`, `eddy`, `bias`) when all expected inputs are present.

## QC Usage

Generate a cohort-level CSV summary after preprocessing:

```bash
python scripts/preprocessing_qc_report.py --basepath /path/to/data --out qc.csv
```

The QC code reads existing outputs from `dwidenoise`, `eddy`, and `eddy_quad`.
It does not run FSL, MRtrix3, or ANTs.

## Tests

```bash
pytest -q
```

## Preserved vs Parameterized

Preserved from the original scripts: the scientific commands and flags for
`dwidenoise`, `mrdegibbs`, `topup --config=b02b0_1.cnf`, `bet -f 0.3 -R -m`,
`eddy_openmp ... --repol --ol_type=both --cnr_maps --residuals`, `eddy_quad`,
and `dwibiascorrect ants ... -nthreads 16`.

Parameterized: data root, subject names, session label, thread counts, and the
sidecars generated from data. The eddy `index` length is derived from the DWI
NIfTI instead of being hardcoded as 181 volumes. `acqparams` and `slspec` are
generated from JSON sidecars.

## AI Use Statement

Parts of this repository's code and documentation were developed with assistance
from AI tools for coding and documentation refinement. The preprocessing design,
scientific decisions, and validation on data remain the author's responsibility.
