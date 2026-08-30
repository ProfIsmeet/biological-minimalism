# Sensor & Channel Taxonomy — Frozen Definitions

**Status: frozen as of this document's creation.** This is Priority 0 of
`TECHNICAL_HANDOFF_V2.md` §18 — decided before any code touches `MODALITIES`
(`backend/app/ml/models.py`) or the dashboard's sensor list, specifically to prevent
"7 sensors vs 4 sensors" confusion (handoff §18 P0). Full rationale for each
per-channel decision is in `TECHNICAL_HANDOFF_V2.md` §3–4; this document is the
short, checkable reference everything else points back to.

## The four category types

### 1. Physiological sensing channel
A channel whose primary purpose is measuring the body's own physiological state —
this is what the CNN+Transformer fusion architecture (PDD Sections 10–11) treats as
a modality token.

| Channel | Status |
|---|---|
| EEG | Core (original abstract) |
| PPG | Core (original abstract) |
| Bio-impedance (BioZ) | Core (original abstract) |
| Skin temperature | Core (original abstract) — **not** validated core-body temperature (§3.4) |
| ECG | Added (handoff §3.1) — if cardiovascular targets remain |

### 2. Context / artifact-reference channel
A channel that informs signal-quality scoring and interpretation of the physiological
channels above, but is not itself treated as an equal fusion-model token. May enter
the model as a low-frequency feature or a context encoder input, not a
`Conv1DEncoder`-style modality token, unless a specific design later justifies
otherwise.

| Channel | Role |
|---|---|
| IMU | Motion-artifact reference (esp. wrist PPG), activity/context, signal-quality support |
| Light | Circadian-relevant external driver, low mass/power/burden |
| Cabin CO₂ | Environmental context |
| Ambient temperature/humidity | Environmental context |

### 3. Contact region
A distinct area of skin contact required by one or more channels. Minimizing contact
regions (not raw sensor count) is closer to this project's actual operational-burden
claim (handoff §1).

| Region | Channels using it |
|---|---|
| Chest | ECG, thoracic BioZ/ICG, IMU (Module A) |
| Wrist/finger | PPG, IMU, skin temperature, light (Module B) |
| Forehead/scalp | EEG (Module C) |
| Leg (experimental) | Segmental BioZ (Module D — not in the core architecture yet) |

### 4. Wearable module
A physical package grouping one or more channels at one contact region — this is the
unit operational cost (mass, power, donning burden) should actually be counted
against, per handoff §1 and §11's Pareto formulation.

| Module | Channels | Status |
|---|---|---|
| A — Chest patch | ECG, thoracic BioZ/ICG, IMU | Candidate |
| B — Wrist/finger | PPG, IMU, skin temperature, light | Candidate |
| C — Frontal headband | EEG (low-channel), local IMU | Candidate |
| D — Leg (optional) | Segmental BioZ | Experimental/ablation candidate only |
| Cabin sensor (not worn) | CO₂, ambient temp/humidity, light | Reported separately from wearable burden |

## Rules that follow from this taxonomy

1. **IMU and light are never counted as physiological modalities** in sensor-count
   claims or in the fusion Transformer's token set, even though they are software
   inputs to the system (handoff §3.2–3.3).
2. **`MODALITIES` in `backend/app/ml/models.py` only changes when a channel is
   promoted from context/experimental to core physiological** — not automatically
   whenever a new sensor is discussed. Currently: `("eeg", "ppg", "temperature",
   "bioimpedance")`. ECG is the only channel presently decided (handoff §3.1) but not
   yet added to the tuple — that change is scoped to a later sub-phase
   (`TECHNICAL_HANDOFF_V2.md` §18, after Priority 1's dataset research confirms real
   synchronized ECG+PPG data is actually available to train it on; see
   `datasets/DATASET_MATRIX.md`).
3. **Operational-cost accounting (Pareto analysis, §11) uses contact regions and
   wearable modules, not raw channel count** — e.g. adding ECG to the existing chest
   module (if BioZ is already there) is a smaller cost increment than adding a new
   leg module for experimental BioZ.
4. **"7 sensors" vs "4 sensors" framing is retired.** The paper's claim is framed as:
   core physiological channels (currently 4, ECG a pending 5th) plus context channels
   that improve quality/interpretation without inflating the "sensor count" the
   minimalism argument is about.
