# PPG-DaLiA Dataset Replay

## Purpose

Dataset replay feeds previously recorded, synchronized real human sensor data
through the same FastAPI/WebSocket transport used by the synthetic demo. It is a
software and model-integration tool. It is **not** live sensor
streaming, hardware timing validation, microgravity validation, or clinical
accuracy evidence.

## Architecture

```text
TelemetrySource
├── SyntheticSource -> existing MockDataEngine
└── DatasetReplaySource -> one PPG-DaLiA subject/session
                              |
                       DataSourceManager
                              |
                  replay fault injection layer
                    (disabled by default)
                              |
                   synchronized window assembler
                              |
                  validated PPG+IMU HR model
                              |
                  /metrics + /ws/live-feed
```

`DataSourceManager` is the only source selected by the backend tick loop. A
successful subject load atomically switches to replay; a failed real-data load
returns a controlled API error and is never relabeled or replaced with fake
samples. Switching source or subject clears replay history.

The shared raw adapter is `backend/app/data/ppg_dalia.py`. The offline ML loader
imports the same adapter, so preprocessing and runtime replay agree on archive
layout and the pickle's embedded `subject` identity.

## Configure the data path

Download the official original per-subject distribution as described in
`datasets/ppg-dalia/README.md`. Do not use the subject-less Zenodo `.ts`
reformatting.

Set the replay data path to either the official outer zip or an extracted
field-study directory, and point the model path at the validated checkpoint:

```bash
BIOMIN_PPG_DALIA_PATH=/absolute/path/to/ppg_dalia_uci.zip
# or
BIOMIN_PPG_DALIA_PATH=/absolute/path/to/PPG_FieldStudy
BIOMIN_PPG_DALIA_HR_CHECKPOINT_PATH=/absolute/path/to/model_b_ppg_plus_imu_ppg_dalia.pt
```

The default replay channel set is:

| Replay name | Original channel | Rate | Role |
|---|---|---:|---|
| `wrist_bvp` | Empatica E4 BVP/PPG | 64 Hz | physiological |
| `wrist_acc` | Empatica E4 3-axis ACC | 32 Hz | context/artifact reference |
| `chest_ecg` | RespiBAN ECG | 700 Hz | physiological ground-truth reference |
| `wrist_temp` | Empatica E4 temperature | 4 Hz | physiological |

The adapter also understands the recorded `wrist_eda`, `chest_acc`,
`chest_resp`, `chest_temp`, `chest_eda`, and `chest_emg` channels. They are not
added to the product's global modality/sensor taxonomy; they remain identified
raw dataset channels and must be explicitly requested through the API.

The original synchronized pickle is approximately 1.2–1.7 GB per subject.
Python pickle cannot lazily materialize selected fields, so replay loads exactly
one selected subject, retains only selected array references, and releases the
previous subject when switching. Never load pickle files from an untrusted
source; use the official UCI distribution.

## Controls

The Settings page provides source, subject, play, pause, reset, and 1x/5x/10x
controls. The equivalent REST surface is:

| Method/path | Behavior |
|---|---|
| `GET /data-source/state` | active source and replay state |
| `GET /data-source/subjects` | subjects physically present in the configured data |
| `POST /data-source/synthetic` | return to the existing synthetic demo |
| `POST /data-source/replay/load` | load one subject; optional `channels` list |
| `POST /data-source/replay/play` | play/resume |
| `POST /data-source/replay/pause` | freeze position and all channel indexes |
| `POST /data-source/replay/reset` | return position and indexes to zero; remain paused |
| `POST /data-source/replay/speed` | set 1, 5, or 10 |
| `POST /data-source/replay/fault` | enable or replace one typed replay fault |
| `DELETE /data-source/replay/fault` | disable the fault and clear all fault state |

End-of-recording behavior is deterministic: replay stops in `ended` state and
does not wrap. Reset is required before replaying the subject again.

## Timing and transport contract

The synchronized pickle defines a common relative subject timeline beginning at
`t=0`. Replay uses a monotonic master clock anchored at play/resume/speed-change
time. Current position is calculated from absolute elapsed monotonic time rather
than by adding sleep intervals, preventing cumulative scheduler drift.

Each channel retains its native sampling rate and its own integer index. A
WebSocket frame contains all samples that became due since the preceding frame:

- `sample_start_index`
- `start_timestamp_seconds`
- `end_timestamp_seconds`
- `sample_rate_hz`
- original scalar or multi-axis `samples`

No channel is blindly upsampled. Playback speed scales the one shared timeline,
so all indexes advance consistently. The replay duration is the shortest
selected channel duration; this conservative policy keeps every emitted sample
inside the interval shared by all selected synchronized channels.

Transport `timestamp` is Unix wall-clock time. Recorded timestamps are relative
seconds within the PPG-DaLiA session. This distinction avoids claiming hardware
clock precision.

## Replay fault injection

Fault injection is an infrastructure and robustness tool for the real replay
pipeline. It is disabled by default and is applied only after an official
recorded replay frame leaves `DatasetReplaySource`, before the synchronized
PPG+IMU window assembler. Synthetic telemetry never passes through this layer.
Only one fault specification is active at a time; enabling a new specification
clears the old fault's random/reference state and all buffered inference and
replay-history state.

The request schema is:

```json
{
  "fault_type": "packet_loss",
  "target": "ppg",
  "severity": 0.25,
  "seed": 2026
}
```

Targets are `ppg`, `imu`, or `both`. Configuration and per-frame provenance
report the fault type, exact target channels, affected channels, severity,
seed, dropped sample counts, and applied parameters. A valid model prediction
also retains that fault state inside its prediction provenance alongside the
dataset, subject, window, model identifier, checkpoint path/hash, and evidence
level. This identifies signal corruption; it is not a model-confidence or
uncertainty estimate. Model uncertainty remains unavailable (`null`).

| Fault | Exact signal semantics | Model-input policy |
|---|---|---|
| `modality_dropout` | Removes every batch for the selected modality. Severity is ignored and recorded as `1`. | PPG and IMU are both required; either dropout yields explicit `input_unavailable` and no HR. |
| `packet_loss` | Independently drops each native-rate sample with probability `severity`, using the configured seed. Remaining contiguous runs retain original sample indexes and timestamps; gaps are not compressed, interpolated, padded, or reconstructed. | A gap reaches the existing continuity check and prevents a prediction until a later complete contiguous window exists. |
| `frozen_sensor` | Holds the selected channel at its first observed sample value for the fault session. Severity is ignored and recorded as `1`. | Frozen PPG reaches the canonical flat/dead-signal rejection. Frozen IMU is passed as explicitly corrupted IMU; if the canonical model returns HR, fault provenance remains attached. |
| `additive_noise` | Adds seeded zero-mean Gaussian noise. Per-axis sigma is `severity` times the first affected batch's per-axis standard deviation; the exact captured reference and resulting sigma are reported. | Corrupted samples go through the unchanged canonical preprocessing/model contract. No extra confidence is inferred. |
| `saturation` | Captures the first affected batch's per-axis range and symmetrically removes a `severity` fraction around its midpoint; exact fixed clip bounds are reported. Severity `1` collapses the channel to its midpoint. | Corrupted samples go through the unchanged contract; fully clipped PPG reaches flat/dead rejection. |

Random streams are derived from the configured seed plus dataset, subject, and
channel identity. Replaying the same subject from the same activation point
with the same batching, configuration, and seed produces identical corruption.
Replay reset, source switch, subject load/switch, explicit disable, or replacing
the configuration clears captured values, random generators, buffered model
windows, held predictions, and replay history. This prevents a clean session or
another subject from inheriting faulted state.

The dashboard's Settings control can enable/disable a fault, select its type
and target, and configure severity and seed. Active frames carry a visible
`FAULT-INJECTED REPLAY` label. Faulted channel batches retain the original
dataset and subject but use a `fault_injected_*` role; replacement modalities
are never introduced or presented as recorded measurements.

## Provenance and unavailable data

Every replay frame and every raw channel batch includes the dataset and subject
identity. Source metadata also contains:

- `source_type = dataset_replay`
- `display_label = REAL RECORDED DATA — REPLAY MODE`
- dataset name, subject, playback position/state/speed
- channel list, license (`CC BY 4.0`), and UCI DOI
- channels not provided by PPG-DaLiA (`eeg`, `bioimpedance`, `light`)

Synthetic-derived vitals, cognitive state, space-adaptation state, sensor
confidence, and AI confidence are absent (`null`) in replay frames. They are not
filled with zeros or synthetic values. The dashboard shows recorded PPG and real
same-session chest ECG while marking unrelated product modalities unavailable.
The only model-derived replay value is heart rate. It is carried separately as
`heart_rate_prediction`, labeled `AI_ESTIMATED`, and includes dataset, subject,
window, model, and checkpoint provenance. `heart_rate_inference` distinguishes
warming-up, available, missing-input, model-unavailable, and inference-error
states. No confidence or uncertainty value is invented.
Synthetic sensor-health scoring, mission/fault simulation controls, and SHAP
explanations return `409` while replay is active, preventing inactive mock-engine
state from being mistaken for properties of the recorded subject.

## Limitations and next boundaries

- The heart-rate model is terrestrial PPG-DaLiA research output, not a clinical
  device or an astronaut-health validation.
- Fault injection validates software robustness only; no robustness or medical
  conclusion is claimed without a controlled sweep and analysis phase.
- The digital-twin baseline is not built from replay data.
- PPG-DaLiA is terrestrial healthy-adult data, not astronaut or microgravity data.
- Replay validates software flow, not device acquisition, network hardware, or
  clinical accuracy.

A future `RealSensorSource` can implement the same `TelemetrySource` contract. A
future fault-injection layer can sit between the active source and the manager's
downstream consumers without changing the PPG-DaLiA loader.
