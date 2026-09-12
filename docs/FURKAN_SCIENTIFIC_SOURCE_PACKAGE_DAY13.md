# Furkan Scientific Source Package (Day 13)

This is the authoritative science source for writing the paper's Methods,
Results, and Limitations. It is NOT final prose - every number below
traces to a named artifact; never copy a number from chat history instead
of this document or its cited artifacts.

## Methods

### PPG-DaLiA (heart rate, wrist IMU marginal value)

- Dataset: PPG-DaLiA (UCI ML Repository C53890), 15 subjects, free-living activities.
- Split: 10 train / 2 val / 3 test (S14, S2, S9), subject-disjoint.
- Modalities: wrist PPG (BVP, 64Hz), wrist 3-axis accelerometer (32Hz).
- Preprocessing: 8s windows, 2s stride, per-window z-score (PPG), per-axis per-window z-score (IMU).
- Model: `Conv1DEncoder` + `Linear` head; capacity-matched baseline (A_cap, 28,865 params) vs. candidate (B, 29,089 params) - 0.77% residual parameter difference.
- Seeds: 42-46 (5).
- Metric: MAE (bpm), RMSE (bpm) secondary.
- Controls: capacity-matched baseline (A_cap); shuffled-IMU negative control (C, same architecture, IMU windows permuted within-subject).
- Source: `docs/PPG_DALIA_CAPACITY_CONTROL_PREDECLARATION.md`, `results/ppg_dalia_capacity_control.json`.

### PTT (heart rate, second physical PPG site marginal value)

- Dataset: PhysioNet Pulse Transit Time PPG Dataset v1.1.0, 22 subjects, sit/walk/run.
- Split: 15 train / 3 val / 4 test (s2, s9, s14, s20), subject-disjoint.
- Modalities: PPG site 1 (`pleth_1-3`) vs. PPG sites 1+2 (`pleth_1-6`).
- Model: shared `Conv1DEncoder` class, differing only in `in_channels`.
- Seeds: 42-46 (5).
- Metric: MAE (bpm), RMSE secondary.
- Controls: none (architecture is capacity-fair by construction, same convention as Sleep-EDF).
- Source: `results/ptt_ppg_site_ablation.json`, `results/ptt_sensitivity_day11.json`.

### Sleep-EDF primary + shuffled control (5-class sleep stage, EOG marginal value)

- Dataset: PhysioNet Sleep-EDFx sleep-cassette, subjects 00-17 (18 subjects, first night, `E`-batch).
- Split: 12 train / 3 val / 3 test (SC4011, SC4081, SC4131), subject-disjoint.
- Modalities: EEG Fpz-Cz only (A) vs. EEG+EOG horizontal (B) vs. EEG+shuffled-EOG (C, EOG permuted within-subject-and-partition).
- Model: `SleepStageClassifier` (`Conv1DEncoder` + `Linear(5)` head), capacity-fair by construction (1.35% residual parameter difference).
- Seeds: 42-46 (5).
- Metric: macro-F1, balanced accuracy secondary.
- Source: `docs/SLEEP_EDF_EEG_EOG_PREDECLARATION_DAY7.md`, `docs/SLEEP_EDF_SHUFFLED_EOG_PREDECLARATION.md`, `results/sleep_edf_eeg_eog_ablation.json`, `results/sleep_edf_eeg_eog_control_analysis.json`.

### Sleep-EDF prospective secondary holdout

- Cohort: subjects 18-25 (8 subjects), same protocol/batch, never in primary train/val/test, frozen before download or evaluation.
- Evaluation-only: same 15 frozen checkpoints as primary, zero retraining.
- Source: `docs/SLEEP_EDF_SECONDARY_HOLDOUT_PREDECLARATION.md`, `results/sleep_edf_secondary_holdout_evaluation.json`.

### Sleep-EDF EOG x Resp interaction

- Same primary 12/3/3 split. M0=EEG (existing), M_A=EEG+EOG (existing), M_B=EEG+Resp (new), M_AB=EEG+EOG+Resp (new).
- Capacity-fairness safeguard: constant 112 params/channel across all 4 configs, verified before interpretation.
- Source: `docs/INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md`, `docs/INTERACTION_EXPERIMENT_PREDECLARATION_DAY10.md`, `results/sleep_edf_interaction_resp_day10.json`.

## Results (exact canonical numbers)

| Experiment | Baseline | Candidate | Effect | Source field |
|---|---|---|---|---|
| PPG-DaLiA (A_cap->B) | 7.813 MAE | see `results/ppg_dalia_capacity_control.json` aggregate.model_a_cap.mean vs. model_b_original_recomputed_from_multiseed.mean | +0.605 bpm, 5/5 seeds | `ppg_dalia_capacity_control.json` |
| PTT (A->B) | 17.540 MAE | 19.003 MAE | -1.462 bpm (worse), 5/5 seeds | `ptt_ppg_site_ablation.json` aggregate |
| Sleep primary (A->B) | 0.7473 macro-F1 | 0.7693 macro-F1 | +0.0220, 4/5 seeds | `sleep_edf_eeg_eog_ablation.json` aggregate |
| Sleep control (C->B) | 0.7420 macro-F1 | 0.7693 macro-F1 | +0.0272, 5/5 seeds | `sleep_edf_eeg_eog_control_analysis.json` aggregate |
| Sleep secondary (A->B) | 0.6530 macro-F1 | 0.6858 macro-F1 | +0.0328, 5/5 seeds | `sleep_edf_secondary_holdout_evaluation.json` aggregate |
| Interaction | M0=0.7473 | M_AB=0.7583 | interaction=+0.0031 +- 0.0434, 2/5 pos 3/5 neg | `sleep_edf_interaction_resp_day10.json` aggregate |

**Never combine the MAE rows and the macro-F1 rows into one ranking.**

## Sensitivity (exact caveats)

- PPG-DaLiA: no single subject or activity dominates the A_cap->B effect (`results/ppg_dalia_sensitivity_day11.json`).
- PTT: n=4 subjects, excluding s2 flips the aggregate sign (`results/ptt_sensitivity_day11.json`).
- Sleep primary: SC4011 drives most of the aggregate effect (`results/sleep_edf_per_subject_analysis.json`).
- Sleep secondary: more evenly distributed (max subject share 41%), descriptive bootstrap shows the mean stays positive in ~99.98% of resamples but this is NOT a population proof (`results/sleep_edf_sensitivity_day11.json`).
- N3 regression: N2->N3 confusion accounts for ~64% of new false positives, Wake->N3 ~30% (both meaningful); N2->N3 increase is NOT seed-consistent (4/5, not 5/5) (`results/sleep_n3_extended_diagnostic_day11.json`).
- Interaction: heterogeneous across seeds and subjects, no dominant single source (`results/sleep_interaction_sensitivity_day11.json`).

## Reproducibility

- Environment: exact match on Python/torch/scipy/sklearn/mne/wfdb/pandas; numpy patch-version drift documented (`results/day10_frozen_environment_verification.json`, `docs/CLEAN_CLONE_REPRODUCTION_DAY13.md`).
- Dataset fingerprints: 266/266 raw files hashed, 0 committed to git (`results/dataset_fingerprint_manifest_day10.json`).
- Checkpoint archive: 60/60 checkpoints (50 + 10 interaction), both externally durable via private GitHub Releases (`results/final_checkpoint_inventory_day14.json`).
- Clean-clone result: `CLEAN_CLONE_PASS_WITH_MANUAL_DATA_SETUP` - every checkpoint-based reproduction exact, contract rebuild and claim checker both succeed (`results/clean_clone_reproduction_day13.json`).

## Interaction (exact bounded result)

+0.0031 ± 0.0434 (sample SD, n=5 seeds), 2/5 seeds positive, 3/5 negative.
Classified `approximately_additive_or_unresolved`. This is the ONLY
interaction experiment run in this project; two other candidate designs
(PPG-DaLiA IMU×EDA/TEMP, PTT second-site×IMU) were audited as feasible but
deferred (`docs/INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md`).

## Limitations (exact)

1. Every experiment uses a single dataset/recording protocol per target - no cross-dataset replication anywhere in this project.
2. Sleep primary (n=3) and secondary (n=8) are the SAME underlying population/protocol, never independent replication, never pooled.
3. PTT evidence is n=4 subjects, s2-sensitive - the smallest, most fragile subject-level evidence in the project.
4. Robustness testing covers exactly one subject (S14) and 114 specific fault conditions - not a general robustness claim.
5. Interaction evidence covers exactly one candidate pair; global sensor-interaction knowledge remains unestablished.
6. No experiment in this project involves microgravity, spaceflight, or astronaut data.

## Paper-Safe Claim Bank

### SAFE
- "A capacity-controlled analysis found a modest, synchronization-linked benefit from adding wrist IMU to wrist PPG for heart-rate estimation on PPG-DaLiA (5/5 seeds, 3/3 subjects)."
- "Adding a second physical PPG site produced a small, heterogeneous, subject-sensitive negative effect on heart-rate estimation (PTT, n=4 subjects, s2-dependent)."
- "Adding a synchronized EOG channel to EEG improved 5-class sleep-stage macro-F1, confirmed by a matched shuffled-EOG negative control and reproduced on an independent 8-subject holdout from the same dataset."
- "All checkpoint-based canonical results reproduce exactly from frozen checkpoints under a verified frozen environment, including a genuine clean-clone test."
- "An EOG x respiratory-signal interaction experiment for sleep staging found an approximately additive, statistically unresolved interaction term at this sample size."

### UNSAFE
- "IMU sensing is necessary for accurate heart-rate estimation." (no necessity claim ever established)
- "This result replicates on an independent dataset/population." (never true anywhere in this project)
- "This defines the globally minimal sensor set for the mission architecture." (one-at-a-time marginal value ≠ global minimality, see `docs/SENSOR_INTERACTION_LIMITATION.md`)
- "The system has been validated for astronauts / spaceflight / microgravity." (never attempted)
- "The Digital Twin has been validated." (not trained or validated in this track)
- "EOG always improves sleep staging." (N3 regresses; effect concentrated in some subjects)
- "The second PPG site is globally useless for heart-rate estimation." (n=4, heterogeneous, s2-sensitive - not a population claim)

### FUTURE
- Microgravity/spaceflight validation.
- Final wearable hardware selection.
- Global (all-pairs) sensor interaction study.
- System-level Pareto/cost-benefit analysis.
- Trained and validated Digital Twin.

## Exact Paper Table References

| If citing... | Use table | Use figure | Source artifact |
|---|---|---|---|
| Experimental protocols | `results/paper_tables/table1_experimental_protocols.csv` | - | see table provenance field |
| Main marginal-value numbers | `results/paper_tables/table2_main_marginal_value_results.csv` | Figures A, C, D, E | `results/scientific_master_table_day11.json` |
| Subject heterogeneity | `results/paper_tables/table3_subject_heterogeneity.csv` | Figures B, C, F | sensitivity artifacts (Day 11) |
| Reproducibility/provenance | `results/paper_tables/table4_reproducibility_provenance.csv` | - | `results/day10_scientific_reproduction.json` |
| Interaction | `results/paper_tables/table5_interaction_experiment.csv` | Figure I | `results/sleep_edf_interaction_resp_day10.json` |

Furkan should never need to copy a number out of chat history - every
number in this document and the tables above traces to a named JSON
field in a committed artifact.
