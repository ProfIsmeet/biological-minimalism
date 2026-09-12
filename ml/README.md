# `ml/` — Research-Grade Training Scaffolding

This folder is **not** imported by the dashboard's inference path at runtime.
The dashboard defaults to the synthetic `MockDataEngine`; its optional
PPG-DaLiA replay mode reuses the raw subject/archive adapter but intentionally
does not run the trained heart-rate model yet. No real dataset or trained
checkpoint is required to run the synthetic demo (see the root `README.md`).

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

## Priority 2 (Technical Handoff v2 §18): does synchronized IMU help PPG heart-rate estimation under motion?

`train_ppg_dalia_imu_ablation.py` + `datasets/ppg_dalia.py` answer this
project's first formally-scoped research question
(`docs/TECHNICAL_HANDOFF_V2.md` §18 Priority 2): *"How much does synchronized
IMU motion information improve wrist-PPG heart-rate estimation, particularly
under increasing motion corruption?"* — using real PPG-DaLiA data (see
`../datasets/ppg-dalia/README.md`, CC BY 4.0, original per-subject
distribution, **not** the Zenodo `.ts` mirror, which strips subject identity
and cannot support a verified subject-wise split).

```bash
cd ml
python preprocess_ppg_dalia.py         # one-time: cache all 15 subjects (~180 MB)
python train_ppg_dalia_imu_ablation.py --save-checkpoints
```

**Method:** two independently-initialized models, identical architecture
family (both reuse the project's real, unmodified `Conv1DEncoder`; Model B
also reuses `ModalityFusionTransformer`, generalized in this pass to accept
an explicit `n_modalities` rather than being hard-coupled to the dashboard's
global 4-modality tuple — see `backend/app/ml/models.py` and
`docs/TECHNICAL_HANDOFF_V2.md` §16.7/Phase 13 Step B, whose masked-pooling
fix this experiment is the first real exercise of), same hyperparameters,
optimizer, epochs, and seed, same **strict subject-wise split** (10 train /
2 validation / 3 held-out test subjects, partitioned once and saved to
`experiments/ppg_dalia_imu_ablation/subject_split.json` — no window from a
test subject is ever seen during training):

- **Model A — PPG only:** `Conv1DEncoder` → linear head.
- **Model B — PPG + synchronized wrist IMU (accelerometer):** two
  `Conv1DEncoder`s (PPG, IMU) → `ModalityFusionTransformer` → linear head.

Ground truth is the real ECG-derived HR label shipped with PPG-DaLiA (no
other HR source used).

**Real, reproducible result** (3 held-out test subjects, 12,852 real 8-second
windows, config/seed/split/full results in
`experiments/ppg_dalia_imu_ablation/`):

| Model | Held-out MAE | Held-out RMSE |
|---|---|---|
| A — PPG only | 9.090 bpm | 12.523 bpm |
| B — PPG + IMU | **7.032 bpm** | **10.717 bpm** |

IMU improved MAE by **2.058 bpm (≈23% relative reduction)**, held-out,
subject-wise, not cherry-picked.

> **Reconciliation (read this).** The ≈23% figure above is the **single-seed**
> ablation. The **replicated multi-seed aggregate** (5 seeds, see
> `results/ppg_dalia_imu_multiseed_replication.json`) is
> **9.086 → 7.208 bpm ≈ 20.6% relative** — use the multi-seed number for any
> project-facing claim. Also note the A→B (PPG-only → PPG+IMU) comparison is
> **capacity-confounded**: baseline A ≈8k params vs candidate B ≈29k params. The
> capacity-matched **C→B** comparison (shuffled-IMU control vs synchronized IMU,
> 0.776 bpm) is the cleanest current evidence. The full A→B benefit must **not** be
> described as "pure IMU sensor value" until a capacity-matched PPG-only control
> (A_cap) exists.

**Stratified by real motion severity** (accelerometer-magnitude-std
quartiles, computed on the test set's own distribution — this is the
substantive part of the question, not just the global average):

| Motion quartile | A (PPG only) MAE | B (PPG+IMU) MAE | IMU improvement |
|---|---|---|---|
| Q1 — lowest motion | 8.075 | 5.110 | 2.965 bpm (37%) |
| Q2 | 8.296 | 5.928 | 2.368 bpm (29%) |
| Q3 | 8.301 | 7.313 | 0.988 bpm (12%) |
| Q4 — highest motion | 11.688 | 9.775 | 1.913 bpm (16%) |

Reported exactly as observed: **both models get worse as motion increases**
(as expected — motion corrupts PPG), and **IMU helps in every quartile and
for every one of the 3 held-out test subjects individually** (S14: 5.53→5.08,
S2: 9.18→6.26, S9: 12.74→9.81 bpm), but the *size* of the improvement is not
a clean monotonic function of motion severity in this run (biggest absolute
gain at the lowest-motion quartile, not the highest). No narrative is forced
onto this non-monotonic pattern — it is what the held-out data shows.

**Negative control (temporally shuffled IMU):** a third model, Model C, uses
the same PPG+IMU architecture as Model B but with each subject's own ACC
windows randomly permuted among themselves — same per-subject motion
*statistics*, broken true PPG↔IMU timing. This tests whether Model B's gain
comes from genuine synchronization or merely from extra input dimensions.

| Model | Held-out MAE |
|---|---|
| A — PPG only | 9.090 bpm |
| C — PPG + *shuffled* IMU | 7.957 bpm |
| B — PPG + *synchronized* IMU | **7.032 bpm** |

Real, honest, nuanced result — not the clean story either direction would
predict: **Model C lands strictly between A and B**, not close to either
endpoint. Splitting the total A→B gain (2.058 bpm):
- **A→C (1.133 bpm, ≈55% of the total gain):** available even with broken
  temporal alignment — IMU's per-subject motion-level statistics carry real
  information on their own, independent of correct synchronization.
- **C→B (0.925 bpm, ≈45% of the total gain):** only available when PPG and
  IMU are correctly time-aligned — genuine synchronized motion information,
  not just extra input dimensions, contributes roughly half of Model B's
  advantage over PPG-only.

This is reported as observed, not adjusted toward "synchronization is
everything" or "synchronization doesn't matter" — the honest reading is that
both effects are real and roughly comparable in size.

**What this does and does not show:** it is real evidence, on real data with
a genuine held-out subject split, that synchronized wrist IMU measurably
improves PPG-derived heart-rate estimation, including under motion — this
directly supports keeping IMU in the architecture as a context/artifact-
reference channel (`docs/TAXONOMY.md`), consistent with
`docs/TECHNICAL_HANDOFF_V2.md` §3.2's recommendation. It does not establish
this for the dashboard's synthetic mock engine, for any other sensor pair, or
for spaceflight/microgravity conditions — PPG-DaLiA is a terrestrial,
free-living-activity dataset, the same caveat already stated for BIDMC in the
PDD.

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
