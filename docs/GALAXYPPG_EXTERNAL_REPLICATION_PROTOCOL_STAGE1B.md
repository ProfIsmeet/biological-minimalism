# GalaxyPPG External Replication Protocol (Stage 1B)

**Classification: GO**

Full machine-readable facts: `results/galaxyppg_actual_file_audit_stage1b.json`,
`results/galaxyppg_protocol_stage1b.json`.

## Scientific purpose

Independent replication, on a different device/subject family, of this
project's existing PPG-DaLiA finding (`results/sensor_marginal_value_contract.json`,
Day 6-8 IMU ablation): does synchronized wrist IMU add HR-estimation
information beyond a capacity-controlled PPG-only baseline?

## Actual-file verification summary

24 participants, three devices (Galaxy Watch 5, Empatica E4, Polar H10).
Direct Zenodo file browsing was blocked this sprint by a network-egress
timeout to zenodo.org (two independent attempts, ~15-20s each). Verification
instead used the peer-reviewed Scientific Data paper's own **measured**
(not nominal) per-signal sample rates and per-participant completeness
table — the authors' own real-file audit. This project's three actually-
needed signals (E4 BVP, E4 ACC, Polar H10 raw ECG) are reported **complete
for all 24 participants**; the two known data-quality issues (Galaxy Watch5
config error for P01, missing E4 temperature for P02) do not touch any
signal this experiment uses.

## Frozen A/B/C

- **A**: E4 BVP only, single-branch 1D-CNN encoder.
- **B**: A + E4 3-axis ACC, dual-branch encoder, fused.
- **C**: same architecture as B, ACC replaced by a within-subject temporally
  deranged ACC segment (real ACC distribution and subject identity
  preserved; cross-subject mixing and label-informed shuffling forbidden).

Reference: Polar H10 raw ECG R-peaks (not any device-derived HR).

## Split

Grouped subject-wise outer CV, every one of the 24 subjects held out
exactly once — chosen over a single fixed split because a fixed split would
leave only ~4-5 subjects in test, reproducing this project's own documented
small-N sensitivity problem (PTT n=4, QDE n=10).

## Capacity control

Architecture-matched dual encoder; A's smaller parameter count relative to
B/C is disclosed explicitly rather than hidden, per this project's own
historical PPG-DaLiA capacity-confound lesson.

## Open items for Stage 2 (not blocking GO)

1. Confirm cross-device timestamp synchronization method from the actual
   downloaded files (not assumed from file co-location).
2. Confirm real per-session durations before finalizing the 8s/2s windowing
   decision.
3. Freeze the exact within-subject ACC-derangement algorithm and its RNG
   seed derivation (following the `ml/sleep_seed_utils.py` sub-seed pattern,
   adapted to GalaxyPPG's own window/subject structure).

## Metric

Primary: MAE (bpm). Secondary: RMSE (bpm). Frozen before any training.

## Negative-result and forbidden-claim policy

See `results/galaxyppg_protocol_stage1b.json` (`negative_result_policy`,
`forbidden_claims`) and `docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md`.
