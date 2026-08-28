# `ml/` — Research-Grade Training Scaffolding

This folder is **not** used by the dashboard at runtime. The dashboard
(`backend/`) runs entirely on the synthetic `MockDataEngine` and a
transparent rule-based physiology model — no real dataset or trained
checkpoint is required to run the demo (see the root `README.md`).

`ml/` is the training pipeline that a follow-on research phase would use to
turn `backend/app/ml/models.py`'s `BiologicalDigitalTwinNet` (a real,
already-implemented PyTorch CNN + Transformer fusion architecture) into an
actually trained model, using the real datasets scoped in
`docs/PDD_Biological_Minimalism_IAC2026.md` (WESAD, STEW, PulseDB, NASA
OSDR — see `datasets/README.md` for how to obtain each one; none are
bundled in this repository).

## Layout

```
ml/
├── datasets/        One loader module per dataset. Each raises
│                    NotImplementedError with a pointer to
│                    datasets/README.md until real data is downloaded and
│                    the loader's TODO parsing logic is filled in — this is
│                    intentional: no fabricated training results ship here.
├── train.py         Training loop skeleton: builds BiologicalDigitalTwinNet
│                    (imported from backend/app/ml/models.py, not
│                    duplicated), trains against whichever loaders are
│                    available, and saves a checkpoint compatible with
│                    backend/app/ml/inference.py's TorchInferenceEngine.
├── ablation.py       Skeleton for the ablation study design described in
│                    the PDD (full sensor set vs. minimal set, modality
│                    dropout, noise/motion-artifact injection).
└── checkpoints/      Trained .pt files land here (gitignored; empty in
                     this repository).
```

## Running a real training job (future work, out of this task's scope)

```bash
cd ml
pip install -r requirements.txt
# Populate datasets/ per datasets/README.md, then:
python train.py --wesad-dir /path/to/WESAD --stew-dir /path/to/STEW \
                 --epochs 50 --output checkpoints/biotwin_v1.pt

# Point the backend at the trained checkpoint:
# backend/.env -> BIOMIN_MODEL_CHECKPOINT_PATH=../ml/checkpoints/biotwin_v1.pt
```

## A real training run *has* been completed (EEG pathway only)

`train_sleep_edf.py` + `datasets/sleep_edf.py` train the project's real
`Conv1DEncoder` (imported unmodified from `backend/app/ml/models.py`) as a
5-class sleep-stage classifier on real PhysioNet Sleep-EDF EEG data — see
`../datasets/sleep-edfx/README.md` for why Sleep-EDF was substituted for
WESAD (WESAD's two official download links were both dead when checked).

```bash
cd ml
python train_sleep_edf.py --data-dir ../datasets/sleep-edfx/raw --epochs 15
```

**Real, reproducible result** (3 real subjects, 8,281 real 30-second EEG
epochs, subject-level held-out split — 2 subjects trained on, 1 fully unseen
subject tested on, so this is a genuine generalization estimate, not
epoch-level leakage): held-out accuracy **72.6%** on 5-class sleep staging
(Wake/N1/N2/N3/REM), against a 66.2% majority-class (always predict "Wake")
baseline computed on that same held-out subject's actual label distribution
(1,856 of 2,802 test epochs are Wake). Per-epoch held-out accuracy across the 15
training epochs ranged from 41.8% to 78.9% — reported honestly rather than
cherry-picked, because 3 subjects is a small sample and this variance is real,
not hidden. The trained checkpoint is at `checkpoints/eeg_encoder_sleep_edf.pt`
(21 real tensors, not committed — see `.gitignore` — regenerate with the
command above).

**What this does and does not prove:** it proves the project's actual
`Conv1DEncoder` architecture (Section 10 of the PDD) trains on real
physiological data and learns a real, better-than-baseline, subject-general
signal from a single modality (EEG). It does **not** produce a checkpoint the
dashboard's `TorchInferenceEngine` can load — that class expects the full
4-modality `BiologicalDigitalTwinNet` state dict (`train.py`, not
`train_sleep_edf.py`), and no accessible real PPG or bio-impedance dataset was
available in this pass to train the other three modality encoders (WESAD,
needed for PPG/temperature, and NASA OSDR, needed for bio-impedance, remain
future work — see `datasets/README.md`). This run is evidence the
architecture *works* on real data, not yet the deployable multi-modal model.

## Next steps toward the full 4-modality checkpoint

1. Find a working WESAD mirror (or an equivalent open PPG+temperature
   dataset) to train the PPG and temperature encoders the same way.
2. Query the NASA OSDR API for a specific head-down-tilt bed rest or dry
   immersion study with a downloadable bio-impedance-adjacent measurement to
   train the bio-impedance encoder.
3. Once at least two real modality encoders exist, train the full
   `BiologicalDigitalTwinNet` fusion model via `train.py` and point
   `backend/.env`'s `BIOMIN_MODEL_CHECKPOINT_PATH` at the result — no other
   code change is needed (verified: `create_inference_engine()` already
   switches to `TorchInferenceEngine` automatically once that path exists).
4. This project's real `Resp oro-nasal` and `Temp rectal` channels
   (downloaded but unused in this first pass — see
   `../datasets/sleep-edfx/README.md`) are a lower-effort next step than a
   new dataset: they could train the temperature/respiration-relevant
   pathway from data already on disk.

Until then, the dashboard's AI layer remains the documented rule-based
estimator (`backend/app/ml/inference.py`, `RuleBasedInferenceEngine`).
