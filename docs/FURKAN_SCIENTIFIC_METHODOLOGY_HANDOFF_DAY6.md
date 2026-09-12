# Scientific Methodology Handoff — Day 6 (for Furkan/Emir)

This is a concise technical handoff, not the final paper. It summarizes
what Day 6 established, what remains open, and which claims are currently
safe to write into the IAC paper.

## What is now frozen

- PPG-DaLiA subject split (`ml/experiments/ppg_dalia_imu_ablation/subject_split.json`),
  window/preprocessing protocol, and the original single-seed=42 result
  (`results/ppg_dalia_imu_ablation.json`) — unchanged, never overwritten.
- PTT second-PPG-site experiment (`results/ptt_ppg_site_ablation.json`) —
  untouched this cycle, used only as a methodological reference for
  multi-seed reporting conventions.
- The sensor marginal-value methodology (`docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`)
  and machine-readable contract (`results/sensor_marginal_value_contract.json`),
  now updated to incorporate multi-seed replication evidence for the
  wrist-IMU record (see below), still with no universal sensor score.

## What this Day 6 replication established

Independently re-verified the original seed-42 checkpoints reproduce their
recorded metrics exactly, then trained Model A/B/C across 5 independent
training seeds (42-46), holding the frozen subject split, windowing,
preprocessing, architecture, and hyperparameters fixed — only training/
model-initialization randomness varied. See
`results/ppg_dalia_imu_multiseed_replication.json` for full per-seed,
per-subject, per-motion-quartile, and per-activity results, and the Day 6
completion report for the exact numbers and replication-status
classification (`STRONGLY_REPLICATED_POSITIVE` / `REPLICATED_BUT_VARIABLE`
/ `MIXED` / `NON_REPLICATED`, thresholds frozen before training).

## What remains open

- The exact fraction of the IMU benefit attributable to "true
  synchronization" vs. "context/statistics that survive shuffling" remains
  a descriptive decomposition, not a proven causal split (unchanged from
  the original finding; the shuffled-IMU control still shows real residual
  predictive value).
- Whether `table_soccer` remains a stable negative activity across seeds,
  or was seed-specific, is reported explicitly in the multi-seed artifact
  — check `activity_level_consistency.table_soccer` before citing it as a
  stable finding.
- `results/ppg_dalia_fault_robustness.json` ("Experiment C" cited in the
  Day 5 master prompt) still does not exist anywhere in this repository —
  unresolved discrepancy, flagged again in Day 6, not silently dropped.

## Which next experiment has been predeclared

`docs/NEXT_TARGET_EXPERIMENT_PREDECLARATION.md`: single-channel EEG
(`Fpz-Cz`) vs. EEG+EOG for 5-class sleep-stage classification on
Sleep-EDF, chosen over BIDMC respiration (baseline already known weak) and
STEW (access not yet credential-verified). Full frozen protocol is in that
document. **No training for it has been performed.**

## Which claims are safe for the paper (pending final numbers - see completion report)

- A precise, subject-disjoint, multi-seed-replicated statement of whether
  synchronized wrist IMU improves PPG-based HR estimation on PPG-DaLiA,
  with the exact seed-direction count and mean±SD benefit.
- The same, separately, for the shuffled-IMU negative control, with
  explicit non-causal-decomposition language.
- The PTT second-site negative result, already 5-seed replicated
  (unchanged this cycle).

## Which claims remain unsupported

- Any generalization beyond PPG-DaLiA's free-living terrestrial population
  and activities.
- Any spaceflight/microgravity claim.
- Any cross-dataset ranking between PPG-DaLiA and PTT (prohibited by the
  marginal-value methodology).
- Any claim about targets other than heart rate (workload, fatigue, BP,
  fluid shift, circadian - all still `UNVALIDATED` in the evidence matrix).
- Any claim about the predeclared Sleep-EDF experiment's outcome - it has
  not been run.

*(Numeric specifics for the replication result are in the Day 6 completion
report and `results/ppg_dalia_imu_multiseed_replication.json` - this
handoff intentionally does not duplicate large tables that would go stale
if referenced instead of the source artifact.)*
