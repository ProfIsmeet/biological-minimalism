# Emir Integration Handoff — Day 8/9 (Secondary Holdout + Archival Durability)

Precise, implementation-level list of what changed on the scientific side.
This document does not modify Emir's branch or `main` — it is a handoff for
Emir/Claude Code to act on.

## 1. Branch / commit state

- Branch: `day9-sleep-secondary-holdout-ml`, based on the already-pushed,
  accepted `day8-sleep-strengthening-ml` (remote HEAD `110641c`, verified
  matching before this sprint started).
- Commits this sprint (in order):
  1. `851c512` — external checkpoint archival durability (GitHub Release).
  2. cohort-freeze predeclaration commit (docs + `cohort.json`, committed
     before any secondary-holdout file was downloaded or evaluated) — bundled
     into the same commit as (1) by a `git add` ordering slip; both are
     present and correctly ordered relative to the evaluation work that
     follows, so no scientific-integrity issue, just a minor commit-message/
     content mismatch worth knowing about if you inspect history.
  3. secondary-holdout evaluation + scientific-contract update commit.
  4. reproducibility + tests + this handoff (final commit).
- `main` was not touched (still `b02c6db`, same as Day 1). Emir's
  integration branch was not touched.
- Pushed: **only** `day9-sleep-secondary-holdout-ml` (and the
  `day8-checkpoint-archive-v1` tag used for the release), never `main`.

## 2. Checkpoint archival is now externally durable

`archival/biological_minimalism_checkpoints_day8.tar.gz` (50 checkpoints,
3.1MB, SHA256 `5e0661a6d5adcf345dfc86fe4c80138b20df405038a13817c7d97a1189572de4`)
is now also a **GitHub Release asset** on the private repo
`ProfIsmeet/biological-minimalism`, tag `day8-checkpoint-archive-v1`.
Downloaded back and re-hashed — byte-identical. `archival_status` in
`results/checkpoint_archival_verification.json` is now
`LOCAL_VERIFIED_EXTERNALLY_DURABLE` (was
`LOCAL_VERIFIED_NOT_YET_EXTERNALLY_DURABLE`-equivalent before). If you need
the checkpoints on another machine (e.g. your Mac), `gh release download
day8-checkpoint-archive-v1 -R ProfIsmeet/biological-minimalism` gets you the
verified archive without cloning the git history.

## 3. Sensor marginal-value contract updated (additive)

`results/sensor_marginal_value_contract.json` methodology bumped
1.3.0 → **1.4.0**.

- **NEW field**:
  `experiments.sleep_edf_eeg_eog_sleep_stage.prospective_secondary_holdout`
  — full n=8 secondary-cohort result (aggregate, class-level, subject-level,
  outcome classification).
- `experiments.sleep_edf_eeg_eog_sleep_stage.marginal_status.evidence_strength`
  is **unchanged** (`"replicated-with-control"`) — deliberately not
  auto-upgraded. `evidence_strength_rationale` now has an appended sentence
  ending in `prospective_secondary_holdout_supported` if any UI text
  surfaces that rationale string.
- `evidence_matrix.sleep_stage_5class.eog_horizontal_channel.status` is
  **unchanged** (`"POSITIVE_MODEST_WITH_TEMPORAL_ALIGNMENT_CONTROL"`) — the
  secondary holdout did not change this status string; it is documented in
  the new field above instead.
- No other experiment record (`ppg_dalia_imu_hr`, `ptt_second_ppg_site_hr`,
  `ppg_dalia_fault_robustness`) was touched.

If any dashboard/UI text cites the Sleep-EDF result as "confirmed on a
held-out cohort," it can now legitimately add "and an independent 8-subject
holdout cohort from the same dataset" — but must not say "a second dataset"
or "population validated." See `docs/FURKAN_PAPER_HANDOFF_DAY9.md` for exact
do/don't phrasing if this ever reaches paper or UI copy.

## 4. New real data on disk (not committed, gitignored)

`datasets/sleep-edfx/raw/` gained 8 new subjects (SC4181, SC4191, SC4201,
SC4211, SC4221, SC4231, SC4241, SC4251 — PSG + hypnogram each, ~400MB
total), downloaded fresh from PhysioNet (same distribution point already
used by this project, not a new dataset/source). All verified byte-exact
against the server's `Content-Length` before use.

## 5. New artifacts

- `docs/SLEEP_EDF_SECONDARY_HOLDOUT_PREDECLARATION.md` — frozen protocol.
- `ml/experiments/sleep_edf_secondary_holdout/cohort.json` — frozen cohort.
- `ml/evaluate_sleep_edf_secondary_holdout.py` — evaluation script (no
  training).
- `ml/verify_sleep_edf_secondary_holdout_reproducibility.py` — reload +
  re-shuffle + re-evaluate, confirms exact match.
- `results/sleep_edf_secondary_holdout_evaluation.json`,
  `results/sleep_edf_secondary_holdout_reproducibility.json`.
- `docs/SLEEP_EDF_SECONDARY_HOLDOUT_RESULTS.md` — full write-up.
- `ml/tests/test_sleep_edf_secondary_holdout.py` — 20 new tests.
- 3 tests added to `ml/tests/test_sensor_marginal_value_contract.py`.

## 6. Potential merge-conflict files if Emir's branch also touched these

`ml/build_sensor_marginal_value_contract.py`,
`docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`,
`docs/MULTI_TARGET_EVIDENCE_MATRIX_DAY8.md`,
`results/sensor_marginal_value_contract.json`,
`results/checkpoint_archival_verification.json`. All changes in this sprint
to these files are additive (new fields/sections), so a merge should be
low-risk, but flagging them explicitly since they were also touched in
Day 7/8.

## 7. Nothing in Emir's software track needs a code change from this sprint

No frontend/backend/replay/WebSocket/fault-injection/Digital
Twin/dashboard files were touched.
