# Emir Integration Handoff — Day 7 / Accelerated Day 8

Precise, implementation-level list of what changed on the scientific side
that may affect integration/contract consumers. This document does not
modify Emir's branch — it is a handoff for Emir/Claude Code to act on.

## 1. Sensor marginal-value contract updated (breaking-ish change)

`results/sensor_marginal_value_contract.json` methodology bumped
1.1.0 → **1.2.0**. If any integration code reads specific fields:

- `experiments.ppg_dalia_imu_hr.marginal_status.evidence_strength` changed
  from `"preliminary"` to `"replicated-within-dataset"` (this happened in
  Day 6, unaffected by Day 7).
- **NEW field**: `experiments.ppg_dalia_imu_hr.capacity_confound_status`
  — if any downstream code was treating the original ~1.9 bpm PPG-DaLiA
  IMU benefit as a clean number, it should now reference
  `capacity_confound_status.genuine_imu_information_benefit_on_matched_capacity_mae_bpm`
  (≈0.605 bpm) as the more defensible, capacity-controlled figure instead.
- `evidence_matrix.heart_rate_bpm.wrist_imu_accelerometer.status` changed
  from `"POSITIVE"` to `"POSITIVE_REVISED_SMALLER_EFFECT_POST_CAPACITY_CONTROL"`.
- `evidence_matrix.heart_rate_bpm.second_physical_ppg_site_proximal_phalanx.status`
  changed from `"NEGATIVE"` to `"NEGATIVE_AGGREGATE_HETEROGENEOUS_BY_SUBJECT"`.
- **NEW top-level experiment**: `experiments.sleep_edf_eeg_eog_sleep_stage`
  and **NEW evidence_matrix key**: `sleep_stage_5class`.
- **NEW field**: `experiments.ptt_second_ppg_site_hr.sensitivity_analysis`
  (s2 dependence, leave-one-out table, revised claim text).

If any dashboard/UI text currently states the PPG-DaLiA IMU result as
"~23% MAE improvement" or similar, **that specific number should be
updated or caveated** — it is now understood to be ~68% capacity-driven,
not purely IMU-information-driven. See
`docs/PPG_DALIA_CAPACITY_CONTROL_RESULTS.md` for exact language.

## 2. New checkpoints exist (not committed to git, gitignored)

15 new checkpoints in `ml/checkpoints/` (5 capacity-control `A_cap`
seeds, 10 Sleep-EDF baseline/candidate seeds). Full manifest with
SHA256/size: `results/checkpoint_manifest_consolidated.json` (43 total
checkpoints tracked across the whole project's history, 43/43 present
locally as of this handoff — none missing). This is a read-only index for
your archival step (GitHub Release/LFS) — I have not set up that
archival myself, per my role boundary.

## 3. New real dataset on disk (not committed, gitignored)

`datasets/sleep-edfx/raw/` now has 18 real Sleep-EDF subjects (was 3).
If any integration code enumerates available datasets, this count changed.

## 4. Nothing in Emir's software track needs a code change from this sprint

No frontend/backend/replay/WebSocket/fault-injection/Digital
Twin/dashboard files were touched. The only integration-relevant action
is deciding whether/how to surface the revised PPG-DaLiA claim language
and the new Sleep-EDF evidence in any UI copy that currently cites sensor
marginal-value numbers.

## 5. Base-commit discrepancy (please resolve)

This sprint was instructed to start from integration checkpoint `cab0023`
on branch `codex/day2-emir-integration`. **Neither exists in this
repository** (`ProfIsmeet/biological-minimalism`, checked working tree,
`git log --all`, and every local/remote branch). `main` here is still at
the Day 1 commit (`b02c6db`). This branch (`day7-accelerated-ml`) was
built from `origin/day6-ml` instead, as the safest available equivalent.
**Please confirm where the actual integration work lives** (a different
remote/fork?) so future ML-track sprints can be based on the correct,
current integrated state.
