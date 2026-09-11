# Stage 3 Science Completion Report

File companion to the full chat report. See chat response for complete
narrative detail; this file is the tracked repository artifact.

## Summary

- Branch: `stage3-science-completion`, base `58e901174cc88fc79e1bc1d5c9bb4d7aa729a372`.
- Codex audit target `ab798815882ac0723491dc489de2375f8bf5b774`: verified untouched.
- **GalaxyPPG**: real BLOCKER found (6/24 subjects had corrupted reference
  ECG) and fixed; corrected full 6-fold CV under
  `GALAXYPPG_CORRECTED_ELIGIBILITY_CV_PROTOCOL_V2` is now **COMPLETE**:
  `EXTERNAL_REPLICATION_SUPPORTIVE` (participant-level A_cap->B +0.834 bpm,
  12/18 favor B; C->B +0.916 bpm, 13/18 favor B; window-weighted agrees to
  <0.02 bpm; no sign reversal under leave-one-out). Real heterogeneity
  disclosed: 6/18 subjects favor A_cap over B. Both pre-fix results
  (single-fold + full 6-fold CV) remain marked
  `INVALIDATED_BY_REFERENCE_SIGNAL_QUALITY_DEFECT`. The earlier bounded
  single-fold diagnostic (+1.342/+1.629 bpm, 3/3 subjects) is retained as
  `BOUNDED_EXTERNAL_REPLICATION_SUPPORTIVE_DIAGNOSTIC`, not the final
  verdict. 75 new checkpoints externally archived and independently
  redownload-SHA256-verified (75/75 exact match).
- **LBNP**: real training complete. `COMPLETE_NEGATIVE` (thoracic EIS did
  not help; B indistinguishable from its own deranged control). Real
  eligibility correction: n=16→n=12 (pleth-quality).
- **HMC**: real access restored (PhysioNet certificate renewed). 45/151
  recordings downloaded+verified. Full training:
  `PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT`. n=7 bounded diagnostic
  (prior sprint) retained as historical.
- **ds003838**: unchanged (n=3 bounded diagnostic); full-cohort blocker
  quantified this sprint (~93GB/~9.4h).
- Architecture: `UNRESOLVED`. Pareto: `NOT_READY`.
- Codex parent-audit remediation (H-01, H-02, Sections 26-33): all closed
  this sprint — see `docs/STAGE3_CODEX_PARENT_AUDIT_SCIENCE_OWNER_REMEDIATION.md`.
- Test suite: 454 passed, 0 failed, 0 skipped.

## Full detail

See `results/stage3_science_completion_manifest.json`,
`results/sensor_value_master_matrix_stage3_complete.json`,
`docs/STAGE3_DATASET_PROVENANCE_AND_FINGERPRINTS.md`,
`docs/STAGE3_CHECKPOINT_MANIFEST.md`,
`docs/STAGE3_SAFE_UNSAFE_CLAIMS.md`,
`docs/STAGE3_HOSTILE_SCIENCE_REVIEW.md`,
`docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md`.

**Final verdict**: `STAGE3_CORE_AND_PRIORITY_EXTERNAL_SCIENCE_COMPLETE_WITH_LOWER_PRIORITY_EXTERNAL_WORK_PENDING`
— GalaxyPPG's corrected full CV and all Codex remediation are complete;
HMC full-cohort training and ds003838 remain genuinely
`PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT` (out of scope this sprint). This
does not claim full Stage 3 completion — whether HMC/ds003838 are
required before Stage 4 is Emir's decision.

## Codex fail remediation sprint (branch `stage3-codex-fail-remediation`)

A second independent Codex audit of `aaa87c21...` returned
`INDEPENDENT STAGE3 DELTA AUDIT FAIL` (three HIGH findings: GalaxyPPG
participant-C evaluation bug, P01 eligibility justification, LBNP
target-range/C-control non-compliance). All three closed with real fixes,
programmatic strong-consistency verification, and 32 new passing tests —
see `docs/STAGE3_CODEX_FAIL_REMEDIATION_REPORT.md` for full detail.
Updated verdict:
`STAGE3_CODEX_FAIL_REMEDIATION_REPORTED_COMPLETE_PENDING_INDEPENDENT_REAUDIT`.
Test suite: 486 passed, 0 failed, 0 skipped.
