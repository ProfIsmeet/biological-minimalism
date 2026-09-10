# GalaxyPPG — Real Reference-ECG-Quality BLOCKER (found via hostile review of the full 6-fold CV)

**Severity: BLOCKER.** **Status: FIXED (eligibility corrected); full-cohort
retraining under the corrected eligibility is `PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT`.**

## What happened

After completing the real full 6-fold grouped CV
(`results/galaxyppg_hr_full_grouped_cv_stage3.json`), the aggregate
computation produced `NaN` for two subjects (P03, P07) — investigating
this (rather than silently dropping them) revealed the real cause: their
Polar H10 ECG channel is essentially unusable (P03: 5 detected R-peaks
over a real 64-minute recording ≈ 0.08 peaks/min; P07: ECG pinned at
saturation `±20064` for long stretches, 0.83 peaks/min) — compare to
~85-86 peaks/min for genuinely healthy reference subjects (P02, P09,
directly checked).

This prompted checking **every** participant's real R-peak detection
rate, not just the two that produced visible NaNs. Result: **6 of 24
participants (25%) have reference ECG too corrupted for reliable R-peak
detection**: P01 (37.08 peaks/min — just below a physiological floor),
P03 (0.08), P07 (0.83), P15 (6.77), P19 (1.42), P22 (0.47).

## Why this matters

The original eligibility check (`ml/build_galaxyppg_eligibility.py`,
prior sprint) verified file presence and cross-device timestamp overlap
only — it never checked whether the reference ECG signal itself was
usable. For these 6 subjects, the "ground truth" HR windows computed by
`reference_hr_windows` were either empty (correctly producing no windows
- P03/P07, hence the NaN) or, worse, **computed from a handful of
spurious/noise-triggered "R-peaks"** that pass the `>=3 peaks per window`
threshold but do not represent real heartbeats (P01, P15, P19, P22) —
silently injecting near-random HR labels into training and evaluation for
those subjects.

**This directly explains** why P01 was a severe ~32 bpm MAE outlier in
the prior sprint's single-fold diagnostic, and why P15/P19/P22 were the
worst-performing subjects in this sprint's just-completed full 6-fold CV
(P15: 40-53 bpm MAE; P19: 30-36 bpm MAE; P22: 18-24 bpm MAE) — not because
the models genuinely performed badly on these subjects, but because the
labels they were being scored against (and, for the 5 of 6 who fell in a
training fold at some point, trained against) were corrupted.

## Fix

`ml/build_galaxyppg_eligibility.py` now includes a real data-integrity
gate: **minimum 40 R-peaks/minute** (a physiologically defensible floor —
real resting/active adult HR is essentially always ≥40 bpm; anything far
below indicates the reference channel itself is unusable, not a genuine
low heart rate). Rerunning the eligibility check against the real files
gives: **18/24 eligible** (`results/galaxyppg_eligibility_stage2.json`,
regenerated this sprint).

## Disposition of already-completed results

- **Prior sprint's single-fold diagnostic**
  (`results/galaxyppg_hr_external_replication_stage2.json`) and **this
  sprint's full 6-fold CV**
  (`results/galaxyppg_hr_full_grouped_cv_stage3.json`): both **retained,
  unmodified, but explicitly marked `INVALIDATED_BY_REFERENCE_SIGNAL_
  QUALITY_DEFECT`** in this document — their historical/diagnostic value
  (proving the pipeline runs end-to-end, proving the UTC+9 sync fix
  works) is preserved, but their MAE numbers must not be cited as valid
  external-replication evidence.
- Per Section 73: this is a BLOCKER-severity implementation defect fix
  that does **not** alter the frozen scientific question (still: does
  capacity-matched IMU addition help PPG HR estimation) — it corrects a
  data-integrity gap in eligibility. Affected experiments must be rerun
  under the corrected eligibility.

## Corrected rerun

A new frozen split over the 18 real eligible subjects
(`results/galaxyppg_split_stage3_corrected_eligibility.json`) and a
bounded (single-fold, not full 6-fold — time budget) corrected training
run are reported in `docs/GALAXYPPG_STAGE3_CORRECTED_RESULTS.md`. Full
6-fold CV under the corrected 18-subject eligibility remains
`PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT`.
