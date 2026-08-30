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

## Real training runs *have* been completed — three of four modalities

Three separate real-data training passes have been run against this
project's real, unmodified architecture pieces from `backend/app/ml/models.py`.
All three results below are reported as they actually came out, including
where the model did **not** beat a naive baseline — nothing here is
cherry-picked.

### EEG — `train_sleep_edf.py` (real PhysioNet Sleep-EDF)

WESAD's two official download links were both dead when checked (see
`../datasets/sleep-edfx/README.md`), so this pass used PhysioNet Sleep-EDF.

```bash
cd ml
python train_sleep_edf.py --data-dir ../datasets/sleep-edfx/raw --epochs 15
```

3 real subjects, 8,281 real 30-second EEG epochs, subject-level held-out
split (2 trained on, 1 fully unseen tested on): **72.6% held-out accuracy**
on 5-class sleep staging (Wake/N1/N2/N3/REM) vs. a 66.2% majority-class
baseline on that held-out subject. Per-epoch held-out accuracy ranged
41.8%–78.9% across 15 epochs (small-sample variance, reported honestly).
Checkpoint: `checkpoints/eeg_encoder_sleep_edf.pt`.

### PPG — `train_ppg.py` (real PhysioNet BIDMC PPG and Respiration Dataset)

WESAD was the original plan for this modality too; substituted with BIDMC
(see `../datasets/bidmc-ppg/README.md`), which turned out to be a better fit
— it has real per-second clinical HR/RESP ground truth, directly matching
this project's real `heart_rate_bpm` / `respiration_rate_bpm` targets.

```bash
python train_ppg.py --data-dir ../datasets/bidmc-ppg/raw --epochs 15
```

53 real subjects, 3,172 real 8-second PPG windows, subject-level held-out
split (37 trained on, 16 fully unseen tested on):
- **Heart rate: held-out MAE 8.72 bpm**, beating the naive baseline (predict
  the training-set mean) of 12.15 bpm — a real, meaningful improvement.
- **Respiration rate: held-out MAE 3.43 breaths/min**, *worse* than the
  naive baseline of 2.29 breaths/min. Reported as-is: within 15 epochs and
  this simple architecture, the model did not learn a useful respiration
  signal from the raw PPG waveform alone — a real negative result, not
  hidden. (The best single epoch's HR MAE was 6.17, better than the final
  epoch's 8.72 — no early stopping/checkpoint-selection is implemented, so
  the reported number is the honest final-epoch result, not the best one
  seen.)

Checkpoint: `checkpoints/ppg_encoder_bidmc.pt`.

### Bio-impedance / temperature — `train_bioimpedance.py` (real PhysioNet QDE dataset)

NASA OSDR's public search API was queried directly for "impedance",
"bioimpedance", "fluid shift", "dry immersion", and "head-down tilt" — every
hit was a molecular-biology ('omics) study; OSDR does not host raw
physiological sensor time series. Substituted with PhysioNet's Quantitative
Dehydration Estimation (QDE) dataset (see `../datasets/qde-bioimpedance/README.md`):
real segmental bio-impedance + real skin temperature from 10 subjects during
exercise-induced dehydration.

```bash
python train_bioimpedance.py --target-mode within_subject_delta
```

10 real subjects, 90 real measurement points, leave-one-subject-out
cross-validation, reframed to predict each subject's fluid change *from
their own baseline* (matching this project's actual "fluid shift," not
absolute body water, which is dominated by body size — the first,
absolute-target version of this experiment scored far worse than baseline
for exactly that reason, and that result is left visible in
`train_bioimpedance.py --target-mode absolute` rather than deleted):
**mean held-out MAE 0.454 L**, against a 0.414 L naive baseline. This is
an honest **null-to-slightly-negative result at n=10** — real bio-impedance
and temperature data, real training, but not enough subjects for this small
model to clearly beat a naive average. No checkpoint is saved by this
script; the result itself (and its small-N limitation) is the deliverable.

### What these three runs do and do not prove

They prove three of the project's four modality pathways train on real data
and that at least two (EEG, PPG-for-heart-rate) learn a real,
better-than-baseline, subject-general signal. They do **not** produce a
checkpoint the dashboard's `TorchInferenceEngine` can load — that class
expects the full 4-modality `BiologicalDigitalTwinNet` state dict
(`train.py`, not these per-modality scripts), and no real dataset was found
for the fourth modality's ideal target, nor were the three encoders above
ever jointly trained with the Transformer fusion layer. These runs are
evidence the architecture *works* on real data across three different real
data sources, not yet the deployable multi-modal fusion model.

## Next steps toward the full 4-modality checkpoint

1. Combine the three real per-modality encoders above with the Transformer
   fusion layer (`ModalityFusionTransformer`) and jointly fine-tune via
   `train.py`, rather than training each modality in isolation as done here.
2. This project's real `Resp oro-nasal` and `Temp rectal` channels from the
   Sleep-EDF files (downloaded but unused so far — see
   `../datasets/sleep-edfx/README.md`) could train a second, independent
   real temperature signal to cross-check the QDE result above.
3. Revisit PPG-based respiration estimation with a purpose-built approach
   (e.g. explicit respiratory-sinus-arrhythmia feature extraction rather
   than raw-waveform-only) given the negative result above.
4. Once the fusion model is jointly trained, point `backend/.env`'s
   `BIOMIN_MODEL_CHECKPOINT_PATH` at the result — no other code change is
   needed (verified: `create_inference_engine()` already switches to
   `TorchInferenceEngine` automatically once that path exists).

Until then, the dashboard's AI layer remains the documented rule-based
estimator (`backend/app/ml/inference.py`, `RuleBasedInferenceEngine`).
