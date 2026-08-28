# Datasets

This directory is a placeholder for the real, open physiological datasets that the
Biological Minimalism research pipeline (`ml/`) is designed to train and validate
against. **No dataset is downloaded or bundled in this repository** — the dashboard
demo (`frontend/` + `backend/`) runs entirely on the synthetic `MockDataEngine`
(`backend/app/engine/mock_data_engine.py`), so it works fully offline with no
dataset download and no account/credential requirements.

This README documents where to get each dataset for the research/training track
described in the PDD (`docs/PDD_Biological_Minimalism_IAC2026.md`, Dataset Research
section) and in the team's own planning notes
(`../Biological_Minimalism_Yol_Haritasi.md`, §5–§6).

## Target datasets

| Target signal / task | Dataset | Where to get it |
|---|---|---|
| Stress / autonomic balance (EDA, ECG, EMG, respiration, temperature, PPG) | **WESAD** (Wearable Stress and Affect Detection) | https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+and+affect+detection |
| Cognitive workload (EEG) | **STEW** (Simultaneous Task EEG Workload) | https://ieee-dataport.org/open-access/stew-simultaneous-task-eeg-workload-dataset |
| Cuffless blood pressure (PPG + ECG) | **PulseDB** / MIMIC-derived cuffless BP datasets | https://github.com/pulselabteam/PulseDB |
| Respiration, sleep/circadian structure | **PhysioNet Sleep-EDF** (+ WESAD's respiration channel) | https://physionet.org/content/sleep-edfx/ |
| Fluid shift / bio-impedance, spaceflight-analog conditions | **NASA OSDR** (Open Science Data Repository) — head-down-tilt bed rest and dry-immersion studies | https://osdr.nasa.gov/bio/repo/ |
| General physiological signal processing reference | **PhysioNet / PhysioBank** | https://physionet.org/ |

## Known limitation: domain gap

WESAD, STEW, and PulseDB were collected from general civilian or clinical
populations under terrestrial conditions — no microgravity, radiation, or
long-duration isolation. NASA OSDR's bed-rest and dry-immersion analog studies are
the closest real proxy for spaceflight physiology available as open data, but are
comparatively small in volume. This domain gap is discussed honestly in the PDD's
Dataset Research and Risk Analysis sections rather than glossed over — the
Biological Digital Twin's per-subject calibration layer is the proposed mitigation
(pretrain on the general-population datasets above, then adapt to an individual
using a short calibration window), not a claim that the demo dashboard's numbers
are clinically validated.

## Getting the real datasets (for the research track, not required for the demo)

1. Create accounts where required (IEEE DataPort for STEW; NASA OSDR is open
   access with no account needed).
2. Download into `datasets/<name>/raw/` (e.g. `datasets/wesad/raw/`, gitignored —
   see the root `.gitignore`).
3. Point `ml/train.py` (see `../ml/README.md`) at the local path via its
   per-dataset arguments (`--wesad-dir`, `--stew-dir`, `--pulsedb-dir`,
   `--osdr-dir`).

No dataset files are committed to this repository, both because of their size and
because most carry their own redistribution terms — always check each dataset's
license before use.
