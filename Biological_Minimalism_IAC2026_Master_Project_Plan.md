# Biological Minimalism — IAC 2026 Master Project Plan

> AI-Driven Minimal Sensor Architecture for Autonomous Astronaut Health Monitoring

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

