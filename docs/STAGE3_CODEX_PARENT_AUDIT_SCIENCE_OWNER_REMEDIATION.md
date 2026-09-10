# Stage 3 — Codex Parent-Audit Science-Owner Remediation

Consolidated record of every finding from the frozen Codex parent audit
(target `ab798815882ac0723491dc489de2375f8bf5b774`, never amended/rebased/
committed to) that this sprint remediated as `SCIENCE_OWNER`. Per the
master prompt: this remediation updates stale scientific-status wording
only — it does not make or re-make any architecture decision.
`FINAL_ARCHITECTURE` remains `UNRESOLVED` and `FORMAL_PARETO` remains
`NOT_READY`.

## H-01 — Checkpoint namespace/mapping ambiguity

- **Issue**: two genuinely different trained models — İsmet's canonical
  Windows-trained `sleep_edf_baseline_eeg_only_seedfix_v2_seed42.pt` and
  Claude's noncanonical Mac-reproduction checkpoint of the same protocol —
  share an identical filename but have different byte content (different
  SHA256, different size).
- **Fix**: published `results/sleep_v2_checkpoint_accepted_mapping.json`,
  an unambiguous SHA256-keyed mapping distinguishing
  `ACCEPTED_CANONICAL` (5bc7c479...) from
  `NONCANONICAL_PENDING_ISMET_REVIEW` (997bb210...), with an explicit
  `rule_for_future_consumers`: resolve by SHA256, never by filename alone.
- **Artifact**: `results/sleep_v2_checkpoint_accepted_mapping.json`.
- **Test**: `ml/tests/test_stage3_codex_h01_checkpoint_namespace.py` (4
  tests, all passing).
- **Remaining limitation**: none — this is an identity-mapping fix;
  `numerical_results_unchanged: true` is asserted in the artifact itself.

## H-02 — Historical capacity-confounded PPG-DaLiA headline

- **Issue**: the old ~20.6%/23% PPG-only -> PPG+IMU relative-MAE-reduction
  figure (Model A 8,065 params vs. Model B 28,865/29,089 params, not
  capacity-matched) was stated as fact - and in some fields even labeled
  as capacity-controlled - in three sensor-value-matrix JSON files and the
  architecture-evidence-handoff JSON, contradicting the correct wording
  already established in `docs/FURKAN_PAPER_HANDOFF_CANONICAL_DAY9.md`.
- **Fix**: relabeled the figure `HISTORICAL_CAPACITY_CONFOUNDED` everywhere
  it appears, with the real governing capacity-controlled numbers
  (A_cap->B ~0.605 bpm, C->B ~0.776 bpm, both 5/5 seeds) cited alongside an
  explicit "never cite it as a clean IMU effect" warning.
- **Artifacts**: `results/sensor_value_master_matrix_stage4.json`,
  `results/sensor_value_master_matrix_post_stage2_4.json`,
  `results/sensor_value_master_matrix_stage3_complete.json`,
  `results/architecture_evidence_handoff_stage4.json`.
- **Test**: `ml/tests/test_stage3_codex_h02_capacity_confounded_label.py`
  (3 tests, all passing).
- **Remaining limitation**: none — wording/labeling fix only, no numeric
  result changed.

## HMC split-source provenance-pointer fix (Section 26)

- **Issue**: `ml/train_hmc_sleep_a_b_c_bounded_n7.py` wrote leftover
  `split_source`/`reduced_cohort_deviation_doc` string literals from its
  original template-copy source (pointing at stage2 files), even though
  the script's own `SPLIT_PATH` constant correctly used the stage3
  bounded-n7 split.
- **Fix**: corrected both string literals in the source script (for future
  runs) and directly in the already-written
  `results/hmc_sleep_external_replication_stage3_bounded_n7.json`, with an
  added `provenance_correction_note` disclosing the fix.
- **Test**: `ml/tests/test_stage3_codex_hmc_provenance_fixes.py`.
- **Remaining limitation**: none — no training result number changed.

## HMC chronology wording downgrade (Section 27)

- **Issue**: "frozen before any HMC file was opened/downloaded" and
  "preregistered" overstate what actually happened - a real RECORDS index
  listing (filenames only, no scientific content) was fetched before the
  split was constructed.
- **Fix**: downgraded to "the full-cohort split was frozen before bounded
  training/evaluation" in `docs/HMC_STAGE3_SPLIT_STRATEGY_DEVIATION.md` and
  `docs/HMC_PILOT_DISPOSITION.md`, with an explicit note distinguishing the
  filename-only RECORDS fetch from any signal/performance inspection.
  Historical transfer-record docs describing another party's own past
  actions were left untouched.
- **Test**: `ml/tests/test_stage3_codex_hmc_provenance_fixes.py`.

## Freeze-manifest CRLF/LF hash semantics (Section 28)

- **Issue**: `build_scientific_freeze_day14.py::sha256_of()` hashed raw
  bytes, so the manifest's hashes were sensitive to incidental CRLF-vs-LF
  differences across Windows/Linux/macOS checkouts of the same tracked
  text content.
- **Fix**: hash line-ending-normalized content (CRLF -> LF); regenerated
  `results/scientific_freeze_manifest_day14.json`; fixed the pre-existing
  `test_freeze_manifest_hashes_are_valid_and_current` test (in
  `ml/tests/test_day11_14_scientific_parallel.py`) to match.
- **Test**: `ml/tests/test_stage3_codex_h_freeze_manifest_hash_semantics.py`
  (2 tests) + the corrected pre-existing test.

## Environment-snapshot artifact (Section 29)

- **Fix**: added `results/stage3_environment_snapshot.json`, a live
  re-query of the actual training venv during this sprint. No drift from
  the Day-10 `EXACT_FROZEN_ENVIRONMENT` record.

## PPG/PTT cache-provenance (Section 30)

- **Status**: `DOCUMENTED_LIMITATION_NOT_FULLY_REMEDIATED_THIS_SPRINT` —
  full retrofit into `ppg_dalia.py`/`pulse_transit_time_ppg.py`'s cache
  read/write contract was judged too risky mid-sprint (underlies multiple
  already-completed frozen results; no compute budget for a resulting
  re-preprocessing pass under this sprint's one-heavy-job-at-a-time rule).
- **Artifact**: `docs/STAGE3_PPG_PTT_CACHE_PROVENANCE_LIMITATION.md` —
  documents the real gap, existing partial mitigation (mislabeled-file
  refusal), and a recommended future fix.

## Status-vocabulary audit — no unearned "CANONICAL" (Section 31)

- **Method**: grepped every `results/*.json` for `CANONICAL`, manually
  inspected every match.
- **Finding**: no unearned self-promotion found or introduced this sprint;
  every match traces to an already-accepted prior-sprint decision or is an
  explicit anti-canonical disclaimer.
- **Artifact**: `docs/STAGE3_CANONICAL_STATUS_VOCABULARY_AUDIT.md`.

## Consolidated GalaxyPPG/LBNP provenance (Section 32)

- **Artifact**: `results/stage3_galaxyppg_lbnp_consolidated_provenance.json`
  — a machine-readable index (with line-ending-normalized SHA256 per file)
  over all GalaxyPPG and LBNP Stage 1B-3 artifacts.

## Stale architecture-evidence wording (Section 33)

- **Fix**: updated `results/architecture_evidence_handoff_stage4.json`'s
  "wrist PPG + wrist IMU" candidate `replication` field from
  `ATTEMPTED_BLOCKED` to `EXTERNAL_REPLICATION_SUPPORTIVE` (reflecting the
  real corrected-eligibility bounded single-fold GalaxyPPG result); updated
  the "thoracic bio-impedance spectroscopy (EIS)" candidate's
  `demonstrated_targets`/`negative_evidence`/`replication`/`biological_n`/
  `key_uncertainty` to reflect the real resolved `COMPLETE_NEGATIVE` LBNP
  finding (n=12 real actual-file-verified eligible of 16 enrolled).
- **Explicitly not changed**: `FINAL_ARCHITECTURE` remains `UNRESOLVED`;
  `FORMAL_PARETO` remains `NOT_READY`. This was a wording update to match
  already-established real findings, not a new architecture decision.

## What remains outside this remediation's scope

HMC full-151-recording download/training and ds003838 download/training
were explicitly out of scope this sprint (forbidden by the master prompt)
and remain genuinely pending — see
`docs/STAGE3_SCIENCE_COMPLETION_REPORT.md` for their tracked status.
