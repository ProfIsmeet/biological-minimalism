# PPG-DaLiA — real data for the IMU/motion-artifact ablation experiment (Priority 2)

## Source

Reiss, A., Indlekofer, I., Schmidt, P., & Van Laerhoven, K. (2019). Deep PPG:
Large-scale Heart Rate Estimation with Convolutional Neural Networks. *MDPI
Sensors*, 19(14), 3079. https://doi.org/10.3390/s19143079

Distribution: UCI Machine Learning Repository, https://doi.org/10.24432/C53890
(`archive.ics.uci.edu/dataset/495/ppg+dalia`). **License: CC BY 4.0** — open
access, no login/credentialing required (verified by direct download).

15 subjects (8 female, 7 male, 21–55 years old), wrist-worn (Empatica E4: PPG/BVP
@ 64 Hz, 3-axis accelerometer @ 32 Hz, EDA, skin temperature) and chest-worn
(RespiBAN: ECG, ACC, EMG, EDA, temperature, respiration) devices, recorded during
8 real daily activities (sitting, stairs, table soccer, cycling, driving, lunch
break, walking, working) — genuinely synchronized multimodal data from the same
subject/session, satisfying `docs/TECHNICAL_HANDOFF_V2.md` §8's requirement for a
real fusion/ablation claim.

## Why this dataset, not the Zenodo `.ts` mirror

A Zenodo mirror (`zenodo.org/records/3902728`) repackages this data as
sktime/aeon `.ts` regression files. **Verified by inspecting its header
directly:** the `.ts` format has no subject/group field at all — it is
impossible to confirm its pre-made TRAIN/TEST split is subject-disjoint from
the file itself. Per this project's own standing rule and the task's explicit
requirement ("never randomly split overlapping windows from the same subject
across train and test"), this project uses the **original per-subject
distribution** instead, where subject identity is unambiguous
(`data['subject']` inside each pickle, cross-checked against the filename by
`ml/datasets/ppg_dalia.py`).

## Download

```bash
mkdir -p raw_uci && cd raw_uci
curl -sS -o ppg_dalia_uci.zip "https://archive.ics.uci.edu/static/public/495/ppg+dalia.zip"
```

~2.87 GB. **Note:** this endpoint does not support HTTP range requests
(`curl -C -` resume fails with "HTTP range error"); if a download is
interrupted, delete the partial file and restart from zero rather than
attempting to resume.

Structure inside (a zip nested inside the downloaded zip):

```
ppg_dalia_uci.zip
  data.zip
    PPG_FieldStudy/
      PPG_FieldStudy_readme.pdf
      S1/S1.pkl, S1_activity.csv, S1_E4.zip, S1_quest.csv, S1_RespiBAN.h5
      S2/ ... S15/    (same file set per subject)
```

Real, verified pickle structure per subject (`S<N>.pkl`; confirmed directly by
loading `S1.pkl` before writing the loader, not assumed from the paper):

```python
data['subject']                       # str, e.g. "S1"
data['signal']['wrist']['BVP']        # (n, 1) float64 @ 64 Hz  - PPG
data['signal']['wrist']['ACC']        # (n, 3) float64 @ 32 Hz  - wrist IMU
data['label']                         # (n_windows,) float64 - real ECG-derived
                                       #   HR, one value per 8s window / 2s step
data['activity']                      # (n, 1) float64 @ 4 Hz - real activity ID 0-8
```

`ml/preprocess_ppg_dalia.py` streams each subject's `.pkl` directly out of the
nested zip (never writing the ~1.2–1.7 GB raw file to disk) and caches compact
per-subject `.npz` windows to `processed/` (also gitignored — see root
`.gitignore`'s `datasets/*/*` pattern).

## Real result

See `ml/experiments/ppg_dalia_imu_ablation/` for the full, honest,
version-controlled result (config, seed, subject split, MAE/RMSE overall +
per-subject + stratified by motion severity) and `ml/README.md` for the
narrative summary.
