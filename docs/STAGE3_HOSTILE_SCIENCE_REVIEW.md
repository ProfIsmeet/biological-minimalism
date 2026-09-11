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
   - **Current disposition**: `FIXED` for the bounded single fold. The
     full corrected-eligibility 6-fold CV, previously
     `PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT`, is now
     `COMPLETE_EXTERNAL_REPLICATION_SUPPORTIVE` (see the dedicated Stage 3
     GalaxyPPG Corrected Full-CV Completion review section below).

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

---

## Stage 3 GalaxyPPG Corrected Full-CV Completion + Codex Remediation —
## This Sprint's Hostile Review

Full corrected 6-fold CV completed this sprint (see
`results/galaxyppg_corrected_full_cv_result.json`). Attacked every vector
required by this sprint's master prompt; findings below. No prior finding
in this document is erased or altered.

### BLOCKER

None found this sprint.

### HIGH

None found this sprint.

### MEDIUM

1. **Effect size shrank substantially from the bounded diagnostic to the
   full CV** (A_cap->B: +1.342 bpm on 3/3 subjects -> +0.834 bpm on 12/18
   subjects; C->B: +1.629 -> +0.916 bpm). This is not a defect - it is
   exactly the risk a bounded single-fold diagnostic cannot rule out, and
   is why the master prompt required the full CV before any final
   classification. Disclosed prominently, not minimized: 6/18 subjects
   favor A_cap over B and 5/18 favor C over B under the full cohort. The
   `EXTERNAL_REPLICATION_SUPPORTIVE` classification is retained because no
   aggregation method or leave-one-out exclusion reverses the aggregate
   sign, but flagged here as a real reduction in the strength of the
   claim relative to what the bounded diagnostic alone would have
   suggested.

### LOW

None found this sprint.

### INFO — attack vectors checked, no finding

1. **Reference-quality threshold hindsight risk**: the full CV's real,
   heterogeneous (not uniformly clean) result is itself evidence against
   outcome-shopping on the 40 peaks/min threshold - an outcome-tuned
   threshold would more plausibly have produced an artificially clean
   result, not one with 6/18 subjects disagreeing with the majority
   direction. `no_performance_outcome_used: true` in
   `results/galaxyppg_corrected_eligibility.json`, and the threshold
   justification's real-gap argument (Section 5/6 of this sprint) predates
   any full-CV number by construction.
2. **Corrected cohort membership**: verified programmatically
   (`ml/tests/test_stage3_galaxyppg_corrected_cv_protocol.py`) that the 18
   fold-assigned subjects exactly match the 18 eligible subjects in
   `results/galaxyppg_corrected_eligibility.json`, with no duplicates and
   no omissions.
3. **Group leakage**: directly checked train/val/test subject-set overlap
   for all 6 folds in `results/galaxyppg_corrected_full_cv_result.json` -
   zero overlap in every fold.
4. **Invalid-checkpoint reuse**: the 75 new `correctedcv_v2` checkpoints'
   file mtimes span 2026-09-10 21:53 to 2026-09-11 01:28 (~3.5h), inside
   this sprint's actual training window - not pre-existing files
   coincidentally matching the new naming pattern.
5. **Model-capacity mismatch**: `ml/train_galaxyppg_corrected_full_cv.py`
   reuses the same `PPGCapacityMatchedModel`/`PPGPlusIMUModel` classes as
   the already-capacity-verified bounded diagnostic (A_cap 28,865 vs
   B/C 29,089 params, 0.77% residual, re-confirmed above under "Capacity-
   fairness re-confirmation") - no new architecture was introduced for the
   full CV.
6. **C-control validity**: condition C uses `PPGPlusIMUModel` with
   deranged/shuffled IMU input. Mean C MAE (8.357 bpm) is worse than mean
   B MAE (7.452 bpm) at the participant level, and C favors B in 13/18
   subjects (vs. B favoring itself, trivially) - the negative control
   behaves as expected (deranged input does not help), not as a leakage
   symptom.
7. **Participant domination**: window-weighted (33,813 pooled test
   windows) and participant-level (n=18, equal-weighted) aggregates agree
   to within 0.02 bpm on both A_to_B and C_to_B - no evidence that
   subjects with more windows are driving the result.
8. **Seed-vs-biological-n confusion**: `results/galaxyppg_corrected_full_cv_result.json`
   keeps `n=18` (biological participants) and `n_seeds=5` in structurally
   separate fields throughout (`aggregate_across_all_18_eligible_subjects`,
   `window_weighted_aggregate.per_fold.*.n_test_windows_this_fold`,
   `runs.*.seed*`) - never conflated.
9. **Old invalidated GalaxyPPG results leaking into current claims**:
   grepped every doc/results file for the pre-fix invalidated result's
   experiment ID and the `INVALIDATED_BY_REFERENCE_SIGNAL_QUALITY_DEFECT`
   marker - all real matches are explicit disclosure/history references,
   none present the invalidated numbers as current.
10. **Old ~23% PPG headline**: covered by H-02 remediation and its
    regression test, re-run and passing after this sprint's further edits
    to the same files.
11. **Checkpoint collision**: `correctedcv_v2` naming is disjoint from
    both `galaxyppg_hr_fullcv_fold*` (pre-fix, invalidated) and
    `galaxyppg_hr_corrected_*` (bounded single-fold diagnostic) -
    confirmed by direct listing, no shared basenames.
12. **HMC chronology**: covered by Section 27 remediation and its
    regression test.
13. **Stale provenance**: spot-checked `ml/train_galaxyppg_corrected_full_cv.py`
    for the same class of leftover-template-string-literal bug found in
    the HMC trainer (Section 26) - its output JSON's descriptive fields
    (`experiment_id`, `frozen_folds`, `fold5_reuse_note`) were manually
    rewritten for this script (not left over from the sed-copy source),
    and were checked against the actual `FOLDS_PATH`/`SINGLE_FOLD_RESULT_PATH`
    constants used - no discrepancy found, aside from the already-disclosed
    stale `aggregate_across_all_24_subjects` key name (fixed post-hoc with
    an explicit correction note, see the full-CV completion commit).
14. **Architecture overclaim**: `final_architecture_status` in
    `results/architecture_evidence_handoff_stage4.json` remains
    `UNRESOLVED` and `formal_pareto` in
    `results/stage3_science_completion_manifest.json` remains `NOT_READY`
    after this sprint's wording updates - verified directly, not merely
    asserted.

