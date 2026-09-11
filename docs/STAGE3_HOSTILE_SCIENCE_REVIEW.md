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

---

## Stage 3 Codex Fail Remediation Sprint — Hostile Review

Full attack list per Part X of the remediation master prompt.

### BLOCKER

None found this sprint.

### HIGH

None remaining - the three inbound HIGH findings (HIGH-01/02/03) were
closed with real fixes, strong-consistency/programmatic verification, and
tests. See `docs/STAGE3_CODEX_FAIL_REMEDIATION_REPORT.md` for full detail.

### MEDIUM

1. **LBNP A_minus_B is genuinely sign-sensitive** (subject 9 exclusion
   flips it) - disclosed prominently in the v2 result and completion
   report, not smoothed over. The more diagnostic C_minus_B comparison is
   robust, which is why the overall classification remains
   COMPLETE_NEGATIVE, but this MEDIUM is recorded rather than hidden.
2. **Section 27 provenance-field expansion incomplete**: the consolidated
   GalaxyPPG/LBNP provenance artifact was not expanded to the full field
   list this sprint's master prompt requested (timezone evidence,
   frequency-axis evidence, etc.) - disclosed as PARTIAL, not falsely
   closed.
3. **Quarantine transfer history correction not re-attempted**: Section 30
   asked to correct a historical claim about file-by-file cherry-picking
   if current docs still repeat it - not re-audited this sprint; status
   OPEN.

### LOW

1. HMC's 59/151 current count was not independently SHA256-re-verified
   this sprint (explicitly out of scope) - the inventory artifact
   discloses this limitation rather than implying full verification.

### INFO — attack vectors checked

1. **P01 performance leakage**: `results/galaxyppg_reference_ecg_qc.json`
   contains no performance field of any kind (tested,
   `test_no_performance_field_in_qc_artifact`).
2. **Post-hoc threshold tuning**: the composite QC rule's two thresholds
   (40/min, 0.50 agreement ratio) were chosen from natural gaps in the
   real distribution, not swept for a preferred outcome - the rule was
   checked against, not fitted to, P01's membership.
3. **Incorrect QC evidence**: the second detector is a genuinely different
   algorithm (amplitude-threshold `find_peaks`, no derivative/energy
   step) - not a relabeled copy of the primary detector.
4. **Participant C aligned-input recurrence**: verified via strong-
   consistency check (0.00e+00 diff) that the fix, not a new bug, is what
   changed the numbers.
5. **C seed/derangement mismatch**: `deranged_acc_for_subject_at_index`
   is tested directly against `deranged_acc_stable`'s own array-level
   output for an uneven-window-count synthetic case
   (`test_deranged_acc_index_matches_array_level_derangement`).
6. **Fold-5 false provenance**: fixed and tested exact equality against
   the true source (Section 16/37).
7. **Old Galaxy evidence leakage**: fail-closed resolver + 5 tests
   (Section 17/38).
8. **LBNP >60 mmHg leakage**: behavioral filter test + real-data
   verification that 0 out-of-scope windows remain (Section 39).
9. **LBNP same-stage C substitutions**: direct tensor-level check with a
   realistic repeated-stage synthetic case, plus 0-collision verification
   on the real 12-subject data (Section 40).
10. **Subject leakage**: LBNP train/test split is LOSO by construction,
    unchanged this sprint; GalaxyPPG group leakage already verified in
    the prior sprint's hostile review, re-confirmed unaffected since
    fold/subject assignment was not touched by HIGH-01/02/03.
11. **Normalization leakage**: `hr_mean`/`hr_std` (GalaxyPPG) and ridge
    feature standardization (LBNP) are both fit on TRAIN only in every
    script touched this sprint - unchanged from the prior, already-
    verified pattern.
12. **Subject-7 sensitivity**: under the corrected (0-60mmHg-only) LBNP
    dataset, the canceling-outlier pair is subjects 4 and 9, not 4 and 7 -
    a genuine change from filtering out-of-scope data, not an error;
    disclosed explicitly in the remediation doc.
13. **Stale HMC counts**: reconciled to one current count (59/151),
    Section 26.
14. **Status self-promotion**: `ACCEPTED_CANONICAL` found and removed
    (Section 24/29) - the one real instance this sprint's re-audit found.
15. **Checkpoint ambiguity**: Sleep V2 mapping completed to all 20 real
    entries (Section 24).
16. **Freeze-manifest incompleteness**: new Section-32 manifest covers 21
    current-package files, verified all-exist and hash-stable.

---

## Stage 3 Final Source-of-Truth Remediation Sprint — Hostile Review

A second independent Codex re-audit found the corrected LBNP execution
itself valid, but found stale governing references to the superseded
607-window LBNP result still active in integration-facing artifacts, an
imprecise LBNP classification, an HMC count that conflated file-presence
with hash-verification, a stale Galaxy split description, and a
test-count inconsistency between two current documents. All addressed.

### BLOCKER / HIGH

None found or remaining.

### MEDIUM

1. **LBNP classification was too strong**: `COMPLETE_NEGATIVE` implied a
   uniform effect, but both A_minus_B (sign-reverses without subject 9)
   and C_minus_B (shrinks substantially without subject 9) are
   substantially influenced by one subject. Corrected to `COMPLETE_MIXED`
   with the sensitivity disclosed, not smoothed into either a clean
   positive or clean negative framing.
2. **HMC count conflated three different claims**: file-presence (59
   .edf), complete recording pairs (58 - SN060 is a partial download,
   missing its annotation and far smaller than a complete recording), and
   SHA256-verified count (52, unchanged from a prior sprint, not
   re-verified this sprint). Publishing a bare "N/151" number without
   this breakdown is itself a real precision defect - fixed by
   `results/hmc_current_download_inventory.json`'s three-way split.

### LOW

1. Section 20 (quarantine transfer-history correction): searched the
   entire current `docs/*.md` corpus for "cherry-pick"/"file-by-file"/
   "individually selected" language specifically describing the ten-file
   quarantine package - no such live claim was found (the one
   "cherry-picked" hit, in `docs/CLAUDE_AB_REPRODUCTION_ADJUDICATION.md`,
   is an unrelated statement about NOT cherry-picking a result). Recorded
   as verified-clean rather than fabricating a fix for a claim that does
   not currently exist.

### INFO — attack vectors checked

1. **Stale LBNP values search** (`27.62`, `29.86`, `29.83`, `-2.24`,
   `-2.237`, `COMPLETE_NEGATIVE`): every current-governing-artifact hit
   was either fixed to the corrected numbers/classification, or confirmed
   to sit inside an explicit `HISTORICAL`/`SUPERSEDED`/`OUT_OF_PROTOCOL`
   disclosure - zero stale-current hits remain (Section 22, verified by
   `test_no_current_governing_artifact_cites_old_lbnp_numbers_uncontextualized`).
2. **Count reconciliation** (`45/151`, `52/151`, `59/151`, `482`, `486`,
   `16/4/4`, `12/3/3`): HMC's three-way count published; test count
   reconciled to 500 (the true current re-run count after this sprint's
   own additions); Galaxy bounded-diagnostic split description corrected
   from the stale `16/4/4` (a leftover from the pre-correction 24-subject
   design) to the real `12/3/3` used by the actual corrected 18-subject
   split.
3. **Freeze self-consistency**: added a test
   (`test_no_entry_marked_historical_is_a_governing_artifact`) that fails
   if any non-historical `governing_artifacts` key in the freeze manifest
   points to a file whose own `status` field says HISTORICAL/SUPERSEDED -
   directly enforces Section 16's requirement, not merely asserted in
   prose.
4. **Architecture overclaim**: `final_architecture_status` remains
   `UNRESOLVED`, `formal_pareto` remains `NOT_READY` after all this
   sprint's wording/classification updates - verified directly.

---

## Stage 3 Final Governance & Freeze Closure Sprint — Hostile Review

A third independent audit found that governance was not genuinely
fail-closed: the prior `governing_artifacts` map was manually maintained
and had let the superseded LBNP result and the bounded (supporting-only)
Galaxy diagnostic sit alongside genuinely governing entries, and a test
in the prior sprint's own freeze-consistency suite contained a
`if "historical" in key.lower(): continue` key-name bypass - exactly the
anti-pattern real governance systems must not have.

### BLOCKER / HIGH

None found or remaining.

### Structural defect found and fixed this sprint

**The `if "historical" in key.lower()` bypass**
(`ml/tests/test_stage3_final_freeze_self_consistency.py`, prior version):
this test would have silently passed even if a HISTORICAL artifact were
assigned a governing-sounding key name without the substring
"historical" in it - governance depended on how a key was NAMED, not on
the artifact's actual state. Rewritten entirely: the new registry
(`results/stage3_governance_registry.json`) gives every artifact an
explicit `status` field, `ml/stage3_science_resolver.py` resolves purely
from that field, and every test in
`ml/tests/test_stage3_governance_*.py` looks up an artifact's real
registry status before asserting anything - no key-name string matching
anywhere in the governance-validation path.

### MEDIUM

1. **Bounded Galaxy diagnostic was implicitly governing**: the prior
   freeze manifest's `governing_artifacts` dict included
   `galaxyppg_bounded_diagnostic` pointing at the single-fold result,
   alongside the full-CV result - two Galaxy entries in one governance
   map invited exactly the "which one is current" ambiguity this system
   exists to prevent. Fixed: the bounded diagnostic is now `SUPPORTING`
   in the registry and does not appear in `governing_artifacts` at all;
   only `galaxyppg_external_replication` (the full CV) does.
2. **Test-count reporting error**: the prior sprint's report said "20 new
   tests" when the actual delta was 14 (486→500). Corrected in
   `results/stage3_science_completion_manifest.json`'s
   `reconciliation_note`, with the real delta stated for both that sprint
   and this one.

### INFO — hostile probes attempted (Part XII)

All performed against a temp-file copy of the registry, never the real
file on disk (verified: `test_real_registry_file_untouched_by_hostile_probes`).

1. **Resolving old LBNP as current**: `resolve_by_path_or_status` raises
   `GovernanceResolutionError` (status `HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL`).
2. **Resolving invalid pre-QC Galaxy results as current**: both the
   pre-fix single-fold and pre-fix full-CV results raise (status
   `INVALIDATED`).
3. **Noncanonical Mac Sleep reproduction resolving as current**: raises
   (status `NONCANONICAL_REPRODUCTION`).
4. **Two GOVERNING artifacts in one family**: raises `AMBIGUOUS`.
5. **Zero GOVERNING artifacts in one family**: raises `No GOVERNING artifact`.
6. **Governing artifact's file deleted/missing**: raises `does not exist on disk`.
7. **Placing a superseded artifact into the governing map**: structurally
   impossible without also changing its registry `status` field to
   `GOVERNING` - and `test_no_governing_artifact_has_a_non_governing_registry_status`
   would immediately catch any registry edit that tried.
8. **Using old HMC count semantics**: `results/hmc_current_download_inventory.json`
   now publishes the 59/58/52 three-way breakdown with explicit
   `canonical_fields`; all current-facing consumers checked and fixed
   (Section 9).
9. **Stale LBNP narrative docs**: `docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md`,
   `docs/LBNP_STAGE3_HIGH03_REMEDIATION.md`, and `docs/LBNP_STAGE3_RESULTS.md`
   all fixed or banner-marked historical (Sections 3-5).

---

## Stage 3 Acceptance Gate Closure Sprint — Hostile Review

The final acceptance audit found three still-open gates: the resolver
trusted the registry's `GOVERNING` label without independently verifying
the artifact's own content (Gate 3), the freeze builder silently omitted
zero-governing families instead of hard-failing (Gate 4), and the current
Stage-3 handoff's opening section still described LBNP as a plain
negative result (Gate 5).

### BLOCKER / HIGH

None found or remaining.

### Self-caught regression during this sprint's own implementation

While adding real machine-readable `status` fields to known-bad artifacts
(to give the resolver something live to independently check), two of the
target files —
`results/sensor_marginal_value_contract.json` and
`results/sleep_edf_interaction_resp_day10.json` — turned out to be
tracked by the **historical Day-14 freeze manifest**
(`results/scientific_freeze_manifest_day14.json`). Modifying them broke
that manifest's frozen hashes and were caught immediately by the existing
test suite (`test_freeze_manifest_hashes_are_valid_and_current`,
`test_contract_rebuild_is_deterministic`). Both files were reverted
byte-for-byte (`git checkout --`) before this sprint's commit, and their
registry entries were changed to use a registry-only
`artifact_semantic_status` assertion instead of a live `status_field` -
explicitly weaker, and disclosed as such, rather than touching a file
frozen by an earlier, unrelated sprint's own freeze chain. This is
exactly the kind of mistake this project's own test suite exists to
catch, and it worked.

### MEDIUM

None found this sprint beyond the self-caught regression above (fixed
before commit).

### INFO — Gate 3/4/5 closure evidence

1. **Gate 3 (resolver)**: `resolve_governing_path()` now performs an
   independent semantic content check after the registry check. Verified
   directly: relabeling the historical LBNP result as the sole GOVERNING
   entry still fails, because the file's own `status` field says
   `HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL` (`test_stage3_gate3_semantic_and_integrity.py`,
   9 tests). Same defense verified for both invalidated Galaxy results,
   the noncanonical Sleep reproduction, and the bounded Galaxy diagnostic.
2. **Gate 4 (freeze)**: the freeze builder now raises `FreezeBuildError`
   on any required family with zero or multiple governing artifacts,
   rather than silently omitting it (`test_stage3_gate4_freeze_hard_fail.py`,
   4 tests). Two new cross-cutting families (`stage3_claims`,
   `stage3_handoff`) replace the manually appended `CROSS_CUTTING_DOCS`
   list - both are now governed, frozen, and hash-verified like any other
   artifact. Registry family count corrected from the stale "18" to the
   actual **21**, read dynamically everywhere rather than hard-coded.
3. **Gate 5 (narratives)**: the current handoff's opening "What is
   COMPLETE" section itself now states `COMPLETE_MIXED` with the full
   corrected values and sign-sensitivity disclosure - not an appended
   correction. Searched the whole document for
   `COMPLETE_NEGATIVE`/`stable negative`/old numbers presented as current
   - zero hits outside explicit "do not cite" prohibitions.
4. **`resolve_and_verify()` hash-mismatch**: verified directly against a
   real (byte-for-byte-restored) governing file - corrupting
   `lbnp_thoracic_eis_stage3_v2_protocol_compliant.json`'s `A_mean` field
   and re-resolving raises `IntegrityVerificationError: HASH_MISMATCH`;
   the file was confirmed restored to its original bytes afterward.
5. **Science non-regression**: Galaxy A_cap-B=+0.834268, C-B=+0.916231;
   LBNP A=20.972675, B=21.425060, C=20.131778, classification
   `COMPLETE_MIXED` - all confirmed byte-identical to the values at this
   sprint's base commit.

