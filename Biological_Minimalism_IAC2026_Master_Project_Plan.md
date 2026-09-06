# Biological Minimalism — IAC 2026 Master Project Plan

> AI-Driven Minimal Sensor Architecture for Autonomous Astronaut Health Monitoring

> ⚠️ **HISTORICAL PLANNING DOCUMENT (Day-0/1 design hypothesis).** This file records
> the project's *original* framing and is preserved for provenance. Several ideas here
> have since been **superseded** by the evidence-driven methodology now in effect:
> - The "only four sensors" set (EEG/PPG/temperature/BioZ) is a **historical design
>   hypothesis**, not a validated or selected minimal set. The current architecture
>   decision status is **`NOT_READY`**.
> - The **Information Density Index (IDI = information / #sensors)** is a **proposed,
>   superseded** concept — it was *not* adopted, because a single weighted scalar
>   would embed arbitrary value judgments across incomparable burden dimensions
>   (power vs mass vs contacts vs comfort). See `docs/OPERATIONAL_COST_METHODOLOGY.md`.
> - Early single-seed figures (e.g. "≈23%" IMU benefit, "%90" reduction targets) are
>   historical; the replicated multi-seed IMU benefit is **≈20.6%**.
>
> **Current source of truth:** the root `README.md`, the research API
> (`backend/app/research/`), and the immutable artifacts in `results/`.

## Overview

This document captures the complete project roadmap for the IAC 2026 paper and demonstrator.

## Core hypothesis

Current astronaut monitoring relies on many sensors. Our hypothesis is that multimodal AI can infer high-value physiological states from only four sensors:

- Wireless EEG
- PPG
- Peripheral temperature
- Bio-impedance

The key contribution is a **Biological Digital Twin** that learns each astronaut's baseline and continues monitoring even when sensors fail.

## Scientific positioning

This is not a claim of inventing a new neural network. The novelty is the **Biological Minimalism paradigm**: maximizing physiological information per active sensor.

We propose tracking an experimental metric:

IDI = Recovered Physiological Information / Number of Active Sensors

## System architecture

Sensors -> Signal Processing -> CNN Feature Extraction -> Transformer Fusion -> Digital Twin -> Explainable AI -> Dashboard

## Technology stack

- Next.js
- FastAPI
- PyTorch
- SciPy
- SHAP
- SQLite

## Phase roadmap

### Phase 1 — Scientific Foundation

Deliverables:

- Literature matrix
- Dataset inventory
- System requirements

Datasets:

- NASA GeneLab
- NASA Open Data
- PhysioNet
- ESA Bed Rest Studies
- DLR Dry Immersion

### Bio-impedance plan

Search order:

1. PhysioNet
2. OpenNeuro
3. IEEE DataPort
4. Zenodo
5. Figshare
6. Kaggle

Fallback:

Estimated Fluid Shift Risk Index from ESA/NASA analog studies.

### Phase 2 — Signal Processing

EEG:
- Band-pass filtering
- Artifact removal

PPG:
- Peak detection
- HR
- HRV

Temperature:
- Drift correction

Bio-impedance:
- Noise filtering

### Phase 3 — Multimodal AI

1D CNN extracts local features.

Transformer performs cross-sensor attention.

### Phase 4 — Biological Digital Twin

Initial baseline:

48–72 hours

Then:

- Online learning
- Adaptive baseline updates
- Drift detection

### Phase 5 — Explainable AI

Local SHAP implementation.

Dashboard displays sensor contribution.

Example:

- PPG 41%
- EEG 35%
- Temperature 14%
- Bio-impedance 10%

### Phase 6 — Ablation Study

Experiments:

- All sensors
- Four sensors
- Remove EEG
- Remove PPG
- Noise injection
- Motion artifacts

Metrics:

- MAE
- RMSE
- F1
- Robustness
- Information Density

### Phase 7 — Dashboard

NASA Mission Control inspired.

Panels:

- Primary Vitals
- Cognitive Status
- Space Adaptation
- AI Confidence
- Digital Twin

### Phase 8 — Demonstrations

#### Demo 1

Sensor Failure Simulation

PPG goes offline.

AI continues inference.

#### Demo 2

Solar Storm Mode

Modes:

- Earth Orbit
- Lunar Surface
- Deep Space
- Solar Event

#### Demo 3

Digital Twin Evolution

Timeline:

- Day 1
- Day 5
- Day 12
- Day 30

### Phase 9 — NASA comparison

Reference:

NASA EVA-style multi-sensor monitoring.

Comparison dimensions:

- Sensor count
- Resilience
- Explainability
- Hardware simplicity

### Phase 10 — Hardware analysis

Final calculations only.

- Power
- Weight
- Battery
- Information Density

### Phase 11 — Paper

Structure:

1. Introduction
2. Related Work
3. Biological Minimalism
4. Architecture
5. Digital Twin
6. AI Engine
7. Experiments
8. Ablation Study
9. Results
10. Discussion
11. Future Work

### Phase 12 — Poster

Include:

- Architecture
- Dashboard
- Ablation Study
- Sensor Failure
- Digital Twin

### Phase 13 — Technical Handoff v2: Research-Grade Integration

Added after the team's Technical Handoff v2 review of the pushed repository
(`ProfIsmeet/biological-minimalism`). Full detail: `docs/TECHNICAL_HANDOFF_V2.md`.
Team ownership for this phase: **Emir** (dataset scouting, data-source architecture,
replay, fault injection, experiment orchestration, model↔backend integration,
digital-twin logic, dashboard research mode, Pareto visualization) — see handoff §19.

Executed in the handoff's own priority order (§18):

| Sub-phase | Name | Exit Criterion | Status |
|---|---|---|---|
| 13.0 | Freeze terminology/taxonomy | Physiological modality vs. context/artifact-reference channel vs. contact region vs. wearable module formally defined and used consistently before any code touches `MODALITIES` | ✅ Done — `docs/TAXONOMY.md` |
| 13.1 | Target-first dataset research | `datasets/DATASET_MATRIX.md` filled per-candidate (PPG-DaLiA, PulseDB, WESAD re-check, others) using the handoff §9 record template, each entry backed by an actually-attempted access check, not assumed | ✅ Done — PPG-DaLiA accessible & used, PulseDB/WESAD verified blocked |
| 13.2 | First real ablation result | A single narrow, measurable question answered with real data: how much does synchronized IMU improve PPG-derived heart-rate estimation under motion? | ✅ Done — IMU cut held-out HR MAE 9.090→7.032 bpm (≈23%); see `ml/README.md` |
| 13.3 | Research-grade ablation framework | Beyond present/absent: target-specific metrics, missing modality, noise, motion artifact, delay, clock drift, uncertainty delta | Not started |
| 13.4 | `DataSource` refactor | `SyntheticSource` / `DatasetReplaySource` / (future) `RealSensorSource` behind one interface; replay of the four real datasets already on disk (Sleep-EDF, BIDMC, QDE, PPG-DaLiA) with preserved timing | Not started |
| 13.5 | Fix model masking/pooling | `ModalityFusionTransformer` pools only over present-modality positions, not `fused.mean(dim=1)` over everything | ✅ Done, regression-tested, and exercised for real by 13.2's Model B/C |
| 13.6 | Real inference adapter | `TorchInferenceEngine.confidence_and_contribution()` actually calls `self.model(...)` on real buffered windows once they exist, instead of silently returning the rule-based snapshot | Not started |
| 13.7 | Pareto analysis | Only after 13.2–13.6 produce real target-specific results; report a frontier, not a single pre-announced sensor count | Not started |

**Immediate fixes done alongside 13.0** (found during the handoff review, no new
research needed): the PDD's Section 20 Limitations bullet contradicting its own
Section 10.2 (handoff §16.5), and the masking/pooling bug (handoff §16.7 — tracked
formally as 13.5 above, but the code-level fix itself was small enough to do
immediately rather than wait).

**Standing rule reinforced by this phase** (handoff §8, already this project's own
practice): never splice unrelated subjects/datasets into a fake simultaneous
multi-sensor reading. A dataset may pretrain/validate one sub-task; a real fusion
claim requires genuinely synchronized multi-modality data from the same
subject/session.

## Folder structure

```
biological-minimalism/
├── paper/
├── dashboard/
├── ml/
├── datasets/
├── notebooks/
├── docs/
└── results/
```

## Risk management

| Risk | Solution |
|------|----------|
| No bio-impedance dataset | Analog risk index |
| Limited NASA data | Hybrid datasets |
| RL too complex | Online learning |
| Dashboard delay | Mock data |
| Slow explainability | Local SHAP |

## Key references

- NASA GeneLab
- NASA Open Data
- PhysioNet
- ESA Bed Rest Studies
- DLR Dry Immersion
- NASA EVA biomedical monitoring literature

