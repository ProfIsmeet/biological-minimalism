# Scientific Reproduction Guide

Step-by-step guide to reproducing this project's frozen ML results from a
clean clone. Written and verified against a real clean-clone test
(`docs/CLEAN_CLONE_REPRODUCTION_DAY13.md`).

## 1. Environment

Frozen scientific stack (`results/environment_manifest.json`):

- Python 3.13.0
- torch 2.6.0+cpu (CPU-only, no CUDA)
- numpy 2.5.2, scipy 1.18.1, scikit-learn 1.9.0, mne 1.12.1, wfdb 4.3.1, pandas 3.0.5
- OS: Windows Server 2022 (10.0.20348)

```bash
python -m venv .venv
.venv\Scripts\pip install -r ml/requirements.txt
```

**Known drift**: `ml/requirements.txt` pins `torch==2.6.0` exactly but
leaves `numpy>=2.2.1,<3.0` unpinned to an exact patch version. A fresh
install may land on a newer numpy patch (e.g. 2.5.3 instead of 2.5.2) than
the exact frozen manifest. This did not change any reproduced result in
testing, but if exact-version paranoia matters, pin
`numpy==2.5.2` explicitly before installing.

**Windows CRLF note**: this repo has `core.autocrlf=true`. Any script or
test that hashes a checked-out *text* file (not a binary checkpoint) and
compares it to a frozen SHA256 constant must normalize line endings first
(`data.replace(b"\r\n", b"\n")`) or it will produce a false-positive
mismatch on Windows. See `ml/build_sensor_marginal_value_contract.py`'s
`_sha256()` for the reference implementation. Binary checkpoints (`.pt`)
are never affected by this (git does not text-normalize them).

**Mac vs. Windows**: the actual scientific training/evaluation environment
is this Windows machine's venv. A Mac integration environment (different
Python/torch version) exists for systems/dashboard work but has never
produced or reproduced any frozen ML result - do not use it to attempt ML
reproduction.

## 2. Datasets

None are committed to git (all gitignored). Obtain each from its
documented source:

- **PPG-DaLiA**: `datasets/ppg-dalia/README.md` - UCI archive zip
  (`archive.ics.uci.edu/static/public/495/ppg+dalia.zip`, ~2.8GB).
- **PTT**: `datasets/pulse-transit-time-ppg/README.md` - PhysioNet Pulse
  Transit Time PPG Dataset v1.1.0, per-subject `.dat`/`.hea`/`.atr` files.
- **Sleep-EDF**: `datasets/sleep-edfx/README.md` - PhysioNet Sleep-EDFx
  sleep-cassette, 18 primary + 8 secondary-holdout subjects (see
  `docs/SLEEP_EDF_SECONDARY_HOLDOUT_PREDECLARATION.md` for the exact
  secondary subject list/filenames).

After downloading, run the preprocessing/caching scripts once:

```bash
python ml/preprocess_ppg_dalia.py
python ml/preprocess_ptt.py
```

(Sleep-EDF has no separate cache step - `ml/datasets/sleep_edf.py` parses
EDF files directly on each run.)

Verify dataset identity against `results/dataset_fingerprint_manifest_day10.json`
(SHA256 per raw file).

## 3. Checkpoint archive

Checkpoints (`ml/checkpoints/*.pt`) are gitignored. Retrieve them from the
two GitHub Releases on the private repo:

```bash
gh release download day8-checkpoint-archive-v1  -R ProfIsmeet/biological-minimalism
gh release download day14-checkpoint-archive-v1 -R ProfIsmeet/biological-minimalism
tar -xzf biological_minimalism_checkpoints_day8.tar.gz
tar -xzf biological_minimalism_checkpoints_day14.tar.gz
# copy checkpoints/*.pt from both extracted archives into ml/checkpoints/
```

Verify against `results/final_checkpoint_inventory_day14.json` (60 total:
50 in the Day-8 archive, 10 interaction checkpoints in the Day-14
archive). Verify hashes with a normal Python SHA256 read - do not rely on
the shell `sha256sum -c` command against the bundled `SHA256SUMS.txt`
files inside these archives on Windows: they were written with the
platform's default text-mode newline, which can embed a `\r` that
`sha256sum -c` treats as part of the filename and fails to open. Hash the
listed files directly instead.

## 4. Builder order

1. `python ml/build_sensor_marginal_value_contract.py`
2. `python ml/build_dataset_fingerprint_manifest.py`
3. `python ml/build_checkpoint_manifest.py`
4. `python ml/check_claim_consistency.py`
5. Any `ml/verify_*_reproducibility.py` script to re-confirm a specific experiment.

## 5. Expected outputs

Every builder writes to `results/*.json` and prints a short summary. A
reproduction script prints `ALL OK` / `ALL CHECKPOINTS REPRODUCED WITHIN
TOLERANCE` when every checkpoint's stored metric matches its freshly
recomputed value exactly (or within the documented float32 tolerance for
the robustness sweep).

## 6. No raw data in git

Never commit anything under `datasets/*/raw/`, `datasets/*/processed/`,
or `ml/checkpoints/`. All are gitignored; keep it that way.
