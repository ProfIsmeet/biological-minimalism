# Frozen Phase 5 protocol: PPG-DaLiA fault robustness

Protocol version: `1.0.0`
Experiment ID: `ppg_dalia_s14_fault_robustness_v1`
Status: frozen before the first complete result run on 2026-09-02.

## Scope and identity

This is a controlled, single-subject characterization of the already-frozen
PPG-DaLiA heart-rate pipeline. The only dataset artifact used is the official
UCI PPG-DaLiA archive and its verified held-out subject `S14`. No other subject
is inferred, fabricated, downloaded, or substituted.

The model is the existing PPG+IMU Model B, with embedding dimension 32, loaded
from `ml/checkpoints/model_b_ppg_plus_imu_ppg_dalia.pt`. The checkpoint must be
exactly 138086 bytes and have SHA256
`c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77`.
The experiment must abort if dataset subject identity or checkpoint identity is
not exact.

## Canonical clean path

Each eligible target label `raw["label"][i]` is the real ECG-derived heart-rate
ground truth for a left-aligned window beginning at `i * 2` seconds. Model input
is raw wrist BVP at 64 Hz (512 samples) plus synchronized raw wrist ACC at 32 Hz
(3 x 256 samples) for the same 8-second interval. Windows have an 8-second
duration and a 2-second stride.

The existing canonical per-window PPG z-score, per-axis IMU z-score, canonical
predictor, training-only HR mean/standard deviation, and frozen checkpoint are
used without modification. There is no retraining, fine-tuning, output clipping,
missing-sample filling, interpolation, fallback HR, or model substitution.

Before fault conditions run, clean results must reproduce both the existing S14
canonical evaluation (`4476` windows, MAE `5.0838541984558105`, RMSE
`7.492855072021484`) and the committed golden integration predictions within
`0.001` bpm. Failure is a stop condition.

## Eligible-window and failure policy

An eligible window is a real S14 label whose full native-rate PPG and IMU spans
exist in the official recording. All eligible windows remain in the availability
denominator for every condition.

- A configured dropout that removes a required modality is `input_unavailable`.
- A full native span that reaches canonical preprocessing but is rejected there
  (for example, flat PPG) is `canonical_invalid_input`.
- A missing sample, index/timestamp discontinuity, non-finite model output, or
  unexpected inference failure is `inference_error`.
- MAE and RMSE are calculated only over explicitly valid predictions.
- Failed windows are never silently excluded, reconstructed, padded, or assigned
  a fabricated prediction.

Ground truth is joined to outcomes only by the verified window index after model
inference. It is never passed to the fault injector, preprocessing functions, or
model predictor.

## Fault application contract

Faults are applied through the accepted Phase 4 `ReplayFaultInjector` to ordered
dataset-replay snapshots before synchronized window assembly. Source sample
indexes and timestamps are preserved. Fault state is reset for every condition.
Input is supplied in fixed non-overlapping 8-second batches; therefore the
accepted first-batch reference standard deviation, clipping bounds, and held
value semantics use the recording's first affected 8 seconds.

Exactly one fault is active in a condition:

| Fault | Targets | Severity | Seeds |
|---|---|---|---|
| clean | none | none | none |
| modality dropout | PPG, IMU, both | 1.00 (binary) | none |
| frozen sensor | PPG, IMU | 1.00 (binary) | none |
| additive noise | PPG, IMU | 0.10, 0.25, 0.50, 1.00 | 2026-2030 |
| saturation | PPG, IMU | 0.10, 0.25, 0.50, 1.00 | none |
| packet loss | PPG, IMU, both | 0.01, 0.05, 0.10, 0.20 | 2026-2030 |

Severity retains the exact Phase 4 meaning: noise is Gaussian sigma as a
fraction of the first affected batch's per-axis standard deviation; saturation
is the fraction of the first affected batch's centered dynamic range removed;
packet loss is independent per-sample loss probability. Saturation 1.00 is the
deliberately extreme full/flat clipping condition.

The matrix has 114 concrete conditions: one clean, five deterministic binary
conditions, forty seeded noise conditions, eight deterministic saturation
conditions, and sixty seeded packet-loss conditions. With 4476 eligible S14
windows this is 510264 condition-window evaluations.

## Metrics and output

For every concrete condition, report eligible count, valid count, availability,
`input_unavailable`, `canonical_invalid_input`, and `inference_error` counts and
rates, valid-only MAE/RMSE, and deltas in MAE/RMSE/availability against clean when
mathematically meaningful. For stochastic condition groups, report the five
per-seed records plus arithmetic mean and population standard deviation across
seeds for availability and available accuracy metrics. Seed variability is not
predictive uncertainty.

The deterministic, machine-readable artifact is
`results/ppg_dalia_fault_robustness.json`; the concise human-readable table is
`ml/experiments/ppg_dalia_fault_robustness/REPORT.md`. Both preserve negative
and unavailable results. No scalar robustness score is defined.

## Claim boundary

The evidence may describe how this frozen pipeline behaves under these
controlled corruptions of official held-out S14 replay data. It cannot establish
population-level robustness, fault tolerance, fault detection, calibrated model
uncertainty, microgravity performance, astronaut readiness, or generalization to
missing subjects.
