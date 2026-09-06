# Pulse Transit Time PPG Dataset — reproducibility README

Parity companion to `datasets/ppg-dalia/README.md`. This is the dataset behind the
**PTT second-PPG-site heart-rate experiment** (`ml/experiments/ptt_ppg_site_ablation/`).
The dataset itself is **not bundled** (see `.gitignore`); this file tells you how to
obtain, verify, and reproduce from it. Full first-audit detail:
[`datasets/PTT_DATASET_AUDIT_DAY3.md`](../PTT_DATASET_AUDIT_DAY3.md).

## 1. Identity & version

- **Name:** Pulse Transit Time PPG Dataset.
- **Version:** PhysioNet page version **1.1.0** (the source `README.txt` internally
  titles itself 1.0.0 — a benign upstream metadata inconsistency, recorded for
  completeness).
- **DOI:** 10.13026/jpan-6n92. Authors: Mehrgardt, Khushi, Poon, Withana
  (University of Sydney).

## 2. Source & license

- **Source (open, unauthenticated HTTP):**
  https://physionet.org/content/pulse-transit-time-ppg/1.1.0/
- **License:** Open Data Commons Open Database License (ODbL) v1.0 — confirmed by
  reading the downloaded `LICENSE.txt`. Redistribution of the raw data is not done
  here; only derived, non-reversible experiment artifacts and checksums are committed.

## 3. File layout (upstream)

- WFDB triplet per record: `sXX_activity.hea` / `.dat` / `.atr`, plus `RECORDS`,
  `README.txt`, `LICENSE.txt`, `ANNOTATORS`.
- A `csv/` subdirectory mirrors each record and adds `subjects_info.csv`.
- **Subjects:** `s1`..`s22` (22 unique, no gaps/duplicates).
- **Records:** `sXX_activity`, activity ∈ {`sit`, `walk`, `run`} → 22 × 3 = **66
  records** exactly.
- **This project uses the WFDB files, not the CSV** (WFDB `.dat` ≈ 452 MB total vs
  CSV ≈ 2.6 GB; `wfdb.rdrecord`/`rdann` give tested parsing).

## 4. Integrity verification

- The upstream distribution ships `SHA256SUMS.txt` covering all
  66 `.hea` + 66 `.dat` + 66 `.atr` + 67 CSV entries — a complete, non-missing set.
- Verify your local copy against that upstream `SHA256SUMS.txt` before preprocessing.
  A repository-side checksum manifest of the exact files consumed is described in
  [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md).

## 5. Split artifact

- Subject-wise held-out split: `ml/experiments/ptt_ppg_site_ablation/subject_split.json`
  (frozen; do not regenerate). This is the authoritative split identity for the
  experiment.

## 6. Preprocessing & reproduction entry points

- `ml/audit_ptt_dataset.py` — real-file audit (headers, binary signal, annotations).
- `ml/preprocess_ptt.py` — windowing/preprocessing into model inputs.
- `ml/train_ptt_ppg_site_ablation.py` — the single-site vs two-site ablation
  (5 optimization seeds).
- `ml/verify_ptt_reproducibility.py` — reloads committed checkpoints and re-evaluates.
- `ml/generate_ptt_report.py` — regenerates the report tables under
  `ml/experiments/ptt_ppg_site_ablation/`.

## 7. Ground-truth derivation

- Heart rate is derived from the record annotations / ECG channel per the frozen
  protocol in `docs/MODEL_CONTRACT_PTT_HR.md`. The experiment compares a single wrist
  PPG site (baseline) against a two-site PPG candidate for HR estimation.

## 8. Known corrections & caveats (do not overstate)

- The aggregate result (single-site baseline beat the two-site candidate across 5
  optimization seeds) is **bounded, heterogeneous negative evidence** — **not** proof
  the second PPG site is useless.
- Subject behavior is heterogeneous; subject **s2** strongly dominates the aggregate
  negative direction, and descriptively removing s2 reverses the aggregate. **Do not
  remove s2** from the analysis and do not report a universal "second site harmful"
  claim.
- The 5 seeds are **optimization replications**, not five independent populations.
- A dedicated leave-one-subject-out sensitivity artifact is expected from the ML track;
  until it exists, use only the numbers already committed in
  `results/ptt_ppg_site_ablation.json`.
- Metrics from PTT and PPG-DaLiA are **not comparable** (different datasets, targets,
  populations, model families) — never rank raw MAE/RMSE across them.
