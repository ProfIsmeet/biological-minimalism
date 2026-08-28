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

No training has been run for this deliverable — the dashboard's AI layer
is the documented rule-based estimator (`backend/app/ml/inference.py`,
`RuleBasedInferenceEngine`) until a real checkpoint exists.
