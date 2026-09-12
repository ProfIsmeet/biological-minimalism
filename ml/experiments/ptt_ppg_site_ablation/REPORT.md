# PTT PPG Site-Value HR Ablation — Full Result Report
## 1. Question
Does a second physical PPG sensor site (proximal phalanx, in addition to the distal phalanx) provide measurable value for heart-rate estimation from PPG alone, evaluated across sitting, walking, and running?
## 2. Frozen design
- Window: 8.0s, stride 2.0s
- Ground truth: ECG R-peak-derived mean HR (>= 3 peaks/window required)
- Preprocessing: per-channel per-window z-score, identical for both models
- Model A channels: ['pleth_1', 'pleth_2', 'pleth_3']
- Model B channels: ['pleth_1', 'pleth_2', 'pleth_3', 'pleth_4', 'pleth_5', 'pleth_6']
## 3. Dataset
PhysioNet Pulse Transit Time PPG Dataset v1.1.0, 22 subjects, 66 records (sit/walk/run), verified against real downloaded WFDB files (see datasets/PTT_DATASET_AUDIT_DAY3.md and the full-dataset audit).
## 4. Split
- Train (15): ['s1', 's4', 's6', 's7', 's8', 's10', 's11', 's12', 's13', 's15', 's16', 's17', 's18', 's19', 's22']
- Val (3): ['s3', 's5', 's21']
- Test (4, held-out): ['s2', 's9', 's14', 's20']
- Window counts: train=10875, val=2204, test=2903
## 5. Model definitions
`PPGSiteHRModel`: one `Conv1DEncoder(in_channels)` + `Linear(embedding_dim, 1)` head. Model A: in_channels=3. Model B: in_channels=6. embedding_dim=32 for both.
## 6. Training protocol
- architecture: PPGSiteHRModel (Conv1DEncoder + Linear head)
- embedding_dim: 32
- optimizer: AdamW
- weight_decay: AdamW default (0.01)
- learning_rate: 0.001
- batch_size: 64
- loss_function: MSELoss (on normalized HR)
- max_epochs: 20
- early_stopping_patience: 5
- checkpoint_selection_metric: val_mae
- validation_metric: val_mae (bpm, un-normalized)
- training_seeds: [42, 43, 44, 45, 46]
- device: cpu
- dtype: float32

## 7. Primary results (overall held-out, mean +/- SD over 5 seeds)
- Model A: MAE 17.540 +/- 1.038 bpm, RMSE 21.190 +/- 1.110 bpm
- Model B: MAE 19.003 +/- 0.411 bpm, RMSE 24.018 +/- 0.781 bpm
- Paired delta MAE (B-A): 1.462 +/- 0.788 bpm (negative = two-site model better)
- Paired delta RMSE (B-A): 2.828 +/- 0.936 bpm

## 8. Per-subject results (seed-aggregated)
| Subject | A MAE | B MAE | Delta MAE | A RMSE | B RMSE | Delta RMSE |
|---|---|---|---|---|---|---|
| s14 | 21.668 | 22.961 | +1.294 | 22.687 | 24.118 | +1.431 |
| s2 | 31.641 | 38.907 | +7.265 | 32.521 | 39.347 | +6.827 |
| s20 | 6.547 | 5.129 | -1.418 | 8.046 | 6.675 | -1.371 |
| s9 | 10.232 | 8.905 | -1.327 | 12.252 | 11.159 | -1.093 |

2/4 held-out subjects improved (lower MAE) with Model B; 2/4 worsened.
Strongest improvement: s20. Strongest regression: s2.

## 9. Per-activity results (seed-aggregated)
| Activity | A MAE | B MAE | Delta MAE | A RMSE | B RMSE | Delta RMSE |
|---|---|---|---|---|---|---|
| sit | 18.912 | 21.407 | +2.494 | 21.379 | 25.059 | +3.680 |
| walk | 17.824 | 17.671 | -0.153 | 20.386 | 22.536 | +2.150 |
| run | 15.883 | 17.914 | +2.031 | 21.754 | 24.361 | +2.606 |

Benefit monotonic with motion (sit < walk < run improvement magnitude): False. This was NOT assumed in advance and is reported as observed.

## 10. Paired per-seed results
| Seed | A MAE | B MAE | Delta MAE | A RMSE | B RMSE | Delta RMSE |
|---|---|---|---|---|---|---|
| seed42 | 17.042 | 19.043 | +2.001 | 20.762 | 24.511 | +3.750 |
| seed43 | 17.744 | 18.844 | +1.100 | 21.614 | 23.380 | +1.766 |
| seed44 | 17.243 | 19.357 | +2.113 | 21.254 | 24.891 | +3.637 |
| seed45 | 16.281 | 18.308 | +2.027 | 19.458 | 22.825 | +3.367 |
| seed46 | 19.391 | 19.462 | +0.071 | 22.862 | 24.481 | +1.619 |

## 11. Negative/unexpected results
See §8-9 above for exact subject/activity-level negatives; 2 of 4 subjects worsened under Model B and any activity with a positive delta above is a case where the second site did not help under this frozen design. Reported as-is.

## 12. Limitations
- Model B has strictly more input channels than Model A by construction - the site-value and channel-count effects are not perfectly separable from PPG channel count alone (disclosed in docs/MODEL_CONTRACT_PTT_HR.md).
- Only 4 held-out test subjects; per-subject estimates carry real sampling uncertainty from a small population.
- 22 terrestrial healthy subjects; no astronaut/microgravity data.
- Windows within a subject/activity are not independent samples - see §16 of the master prompt; no window-level significance testing was performed for this reason.
- s13's ECG-noise caveat (flagged by the original dataset authors) applies to the train split in this frozen assignment; retained per the pre-registered split.
- Held-out subject s2 has a real, verified-from-raw-data HR distribution far outside the training population's range (sit ~121 bpm, run ~140 bpm mean, vs. a train-set mean of ~85 bpm) - a genuine out-of-distribution held-out subject, not a data or leakage issue, but it dominates the small (N=4) held-out aggregate MAE for both models.

## 13. Permitted claims
- A quantified, subject/activity-level marginal comparison of one vs. two PPG sites for ECG-referenced HR estimation on this dataset/split.
- Whether the observed effect (if any) is consistent, seed-stable, and its direction and magnitude, exactly as measured.

## 14. Prohibited claims
- No claim of universal superiority of multi-site PPG, no astronaut/microgravity generalization, no cuffless BP/PTT-as-BP claim, no claim that six channels are globally optimal, no treating seed SD as predictive uncertainty.

## 15. Relationship to Biological Minimalism
Under this frozen experiment, the second physical PPG site did not show a clear mean marginal MAE improvement for ECG-referenced HR estimation (paired delta +1.462 bpm). This is a legitimate, useful negative sensor-value result consistent with the Biological Minimalism hypothesis for this specific target - it does not generalize beyond HR or beyond this dataset.
