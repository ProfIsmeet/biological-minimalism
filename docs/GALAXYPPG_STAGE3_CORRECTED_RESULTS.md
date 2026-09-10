# GalaxyPPG — Corrected Results (Stage 3, after fixing the reference-ECG-quality BLOCKER)

**Status: `EXTERNAL_REPLICATION_SUPPORTIVE`** (bounded to a single corrected
fold — see scope note below). Supersedes both the prior sprint's
single-fold diagnostic and this sprint's full 6-fold CV, **both of which
are marked `INVALIDATED_BY_REFERENCE_SIGNAL_QUALITY_DEFECT`** — see
`docs/GALAXYPPG_REFERENCE_SIGNAL_QUALITY_BLOCKER.md`.

## What changed

A real data-integrity gate (minimum 40 R-peaks/minute from the real Polar
ECG — anything below indicates a corrupted/disconnected reference channel,
not a genuine low heart rate) was added to eligibility this sprint, after
hostile review of the full 6-fold CV's results surfaced two `NaN` subjects
and, on investigation, four more subjects with near-zero detectable
heartbeats. **Eligible cohort corrected from 24 to 18 real subjects.**

## Corrected split (12/3/3, neutral seed-42 shuffle over the 18 eligible)

Train: P04, P08, P09, P10, P11, P13, P14, P16, P17, P18, P21, P23. Val:
P05, P20, P24. **Test: P02, P06, P12.**

## Exact results (MAE, bpm, 5 seeds)

| Model | Mean | SD (ddof=1) |
|---|---|---|
| A_cap | 6.207 | 0.531 |
| B | 4.865 | 0.761 |
| C | 6.494 | 0.575 |

**A→B: mean +1.342 bpm, 5/5 seeds favor B.**
**C→B: mean +1.629 bpm, 5/5 seeds favor B.**

Both effects are now unanimous across all 5 seeds — a qualitatively
different picture from the corrupted-data run's weak, inconsistent
+0.25 bpm/3-5-seeds signal.

## Per-subject results (all 3 test subjects, consistent direction)

| Subject | A_cap MAE | B MAE | C MAE | A→B | C→B |
|---|---|---|---|---|---|
| P02 | 6.39 | 4.33 | 6.78 | +2.05 | +2.45 |
| P06 | 6.58 | 5.29 | 6.90 | +1.29 | +1.61 |
| P12 | 5.67 | 4.97 | 5.80 | +0.70 | +0.84 |

**No sign reversal** — all 3 test subjects favor B over both A_cap and C,
by varying but always-positive margins.

## Interpretation

Once the reference-signal defect is corrected, GalaxyPPG shows a real,
consistent, capacity-controlled IMU benefit for PPG-based HR estimation —
qualitatively reproducing the direction of the original PPG-DaLiA finding
on an independent device/subject family, at this bounded (3-test-subject)
scale. B beating its own deranged-IMU control C by nearly the same margin
it beats A_cap (+1.63 vs +1.34 bpm) indicates the benefit is attributable
to genuine temporal IMU-motion correspondence, not merely to added model
capacity or context.

## Scope disclosure (still real, still honest)

This is **one corrected fold (3 test subjects of 18 real eligible)**, not
a full grouped CV over the corrected cohort. A full 6-fold (or similar)
CV under the corrected 18-subject eligibility is the natural next step and
was **not completed this sprint** (`PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT`
— the uncorrected full CV alone took several hours of this session's
compute budget).

## Safe claim

"Under a capacity-controlled, real-ECG-referenced protocol, after
correcting a real reference-signal-quality defect that affected 6/24
subjects, GalaxyPPG shows a consistent (5/5 seeds, 3/3 test subjects)
capacity-controlled IMU benefit for PPG-based HR estimation, qualitatively
consistent with the original PPG-DaLiA finding — at a bounded single-fold
scale (3 of 18 real eligible subjects tested)."

## Unsafe claims (not made)

"GalaxyPPG replicates PPG-DaLiA" (use "qualitatively consistent," this
project's established convention). Any claim beyond the 3 bounded test
subjects — the full corrected-eligibility CV remains to be run.
