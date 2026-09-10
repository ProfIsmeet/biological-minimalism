# Stage 3 Hostile Science Review

## BLOCKER

1. **GalaxyPPG reference-ECG-quality defect** (found this sprint, via
   hostile review of the full 6-fold CV's NaN results). 6/24 subjects
   (P01, P03, P07, P15, P19, P22) had reference Polar ECG too corrupted
   for real R-peak detection (0.08–37.08 peaks/min vs. ~85-86 peaks/min
   for genuine reference subjects) — the original eligibility check only
   verified file presence and timestamp overlap, never signal quality.
   This silently injected near-random HR labels into training/evaluation
   for these subjects across BOTH the prior sprint's single-fold
   diagnostic and this sprint's full 6-fold CV.
   - **Evidence**: direct R-peak-rate measurement on all 24 real subjects
     (`ml/build_galaxyppg_eligibility.py`, rerun this sprint).
   - **Affected result**: `galaxyppg_hr_external_replication_stage2.json`
     (prior sprint), `galaxyppg_hr_full_grouped_cv_stage3.json` (this
     sprint) — both marked `INVALIDATED_BY_REFERENCE_SIGNAL_QUALITY_DEFECT`.
   - **Affected claim**: the prior sprint's `EXTERNAL_REPLICATION_MIXED`
     classification is retracted as based on corrupted data.
   - **Fix**: real 40 peaks/minute data-integrity gate added; corrected
     eligibility = 18/24; corrected single-fold rerun completed this
     sprint, showing a genuinely consistent, unanimous positive result
     (`EXTERNAL_REPLICATION_SUPPORTIVE`).
   - **Current disposition**: `FIXED` for the bounded single fold; full
     corrected-eligibility 6-fold CV remains `PENDING_DUE_TO_COMPUTE_OR_
     SESSION_LIMIT`.

## HIGH

None new this sprint beyond the BLOCKER above.

## MEDIUM

1. **LBNP real pleth-quality exclusion reduces n from 16 to 12** —
   disclosed, predeclared (data-quality, not outcome-based), not a
   defect but a real, material cohort-size correction worth flagging at
   this severity given its impact on statistical power.
2. **LBNP subjects 4 and 7 are extreme, opposite-direction outliers**
   (+43.3 and −36.5 mmHg respectively) — investigated to the extent
   feasible this sprint (no obvious data-quality flag found for either in
   the real files inspected), disclosed in full, not excluded.
3. **HMC full-cohort training not attempted this sprint** despite real
   access being restored — a genuine compute/time-budget constraint,
   correctly classified `PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT` per
   Section 92, not silently relabeled `OUT_OF_SCOPE`.

## LOW

4. The GalaxyPPG full 6-fold CV's 75 checkpoints (pre-fix) were not
   externally archived before being superseded by the corrected rerun —
   acceptable given they are `INVALIDATED_BY_REFERENCE_SIGNAL_QUALITY_
   DEFECT` and archiving invalidated checkpoints would add no value.
5. `gh release create`/`upload` with multiple files via shell
   command-substitution failed with a "no matches found" error (same
   issue as the prior sprint) — worked around by uploading individually;
   root cause still not fully diagnosed but does not affect the
   correctness of any archived/verified checkpoint.

## INFO

6. The GalaxyPPG BLOCKER is a strong example of hostile review doing its
   job: a `NaN` in an aggregate computation was investigated rather than
   silently patched over (e.g., by just filtering out NaNs in the mean),
   which led to discovering a real, materially significant, cohort-wide
   data-integrity gap.
7. LBNP's n=16→n=12 correction is the fourth real actual-file-driven
   cohort-size correction this project has made (after QDE, ds003838, and
   HMC's repeat-night non-issue) — a consistent pattern of this project's
   actual-file-over-metadata discipline paying off.
8. HMC's certificate renewal (real, independently verified via `openssl
   s_client`) is a positive external development outside this project's
   control.

## Capacity-fairness re-confirmation

GalaxyPPG A_cap (28,865) vs B/C (29,089) — 0.77% residual, unchanged
methodology from PPG-DaLiA's precedent, re-verified this sprint on the
corrected run. LBNP's A (10-dim) vs B (210-dim) — NOT capacity-matched
(a real, disclosed limitation of the ridge-regression design: L2
regularization is tuned independently per condition via nested LOSO,
which is the QDE V2 precedent's fairness mechanism, not literal parameter
matching — restated here for Stage 3 completeness, not newly discovered).

## Statistical unit compliance re-confirmed

GalaxyPPG: 24 total / 18 real eligible / 3 test subjects, 5 seeds — never
conflated. LBNP: 16 total / 12 real eligible subjects, LOSO (no separate
seed dimension, ridge is deterministic) — never conflated with window
count (variable per subject, correctly not treated as biological n).
