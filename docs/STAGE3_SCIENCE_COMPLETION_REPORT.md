# Stage 3 Science Completion Report

File companion to the full chat report. See chat response for complete
narrative detail; this file is the tracked repository artifact.

## Summary

- Branch: `stage3-science-completion`, base `58e901174cc88fc79e1bc1d5c9bb4d7aa729a372`.
- Codex audit target `ab798815882ac0723491dc489de2375f8bf5b774`: verified untouched.
- **GalaxyPPG**: real BLOCKER found (6/24 subjects had corrupted reference
  ECG) and fixed; corrected single-fold result is
  `EXTERNAL_REPLICATION_SUPPORTIVE` (5/5 seeds, 3/3 subjects, no sign
  reversal). Both pre-fix results (single-fold + full 6-fold CV) marked
  `INVALIDATED_BY_REFERENCE_SIGNAL_QUALITY_DEFECT`. Full corrected 6-fold
  CV: `PENDING_DUE_TO_COMPUTE_OR_SESSION_LIMIT`.
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
- Test suite: 430 passed, 0 failed, 0 skipped.

## Full detail

See `results/stage3_science_completion_manifest.json`,
`results/sensor_value_master_matrix_stage3_complete.json`,
`docs/STAGE3_DATASET_PROVENANCE_AND_FINGERPRINTS.md`,
`docs/STAGE3_CHECKPOINT_MANIFEST.md`,
`docs/STAGE3_SAFE_UNSAFE_CLAIMS.md`,
`docs/STAGE3_HOSTILE_SCIENCE_REVIEW.md`,
`docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md`.

**Final verdict**: `STAGE3_SCIENCE_PARTIALLY_COMPLETE_WITH_EXPLICIT_PENDING_AND_BLOCKED_WORK`
