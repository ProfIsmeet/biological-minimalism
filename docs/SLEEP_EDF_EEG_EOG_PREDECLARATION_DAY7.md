# Sleep-EDF EEG vs EEG+EOG — Repaired Predeclaration (Day 7)

**Supersedes the subject-count/access gap in
`docs/NEXT_TARGET_EXPERIMENT_PREDECLARATION.md` (Day 6) for this specific
experiment.** That document's dataset choice, target, and general
rationale are preserved unchanged; this document freezes the exact,
now-fully-resolved protocol before any training.

**Research question:** Does adding a physically distinct EOG channel to a
baseline EEG configuration improve held-out 5-class sleep-stage
classification under a frozen, subject-disjoint protocol? This is a
target- and modality-family diversification of the marginal-value
methodology already used for PPG-DaLiA and PTT (HR, regression) — here
applied to sleep stage (classification, EEG/EOG).

## 9.1 Held-out subject count — RESOLVED

18 real subjects downloaded and verified today from PhysioNet Sleep-EDF
(sleep-cassette), one night each: `SC4001, SC4011, SC4021, SC4031, SC4041,
SC4051, SC4061, SC4071, SC4081, SC4091, SC4101, SC4111, SC4121, SC4131,
SC4141, SC4151, SC4161, SC4171`. Verified: 153 total subject-night codes
exist in the real PhysioNet directory listing
(`https://physionet.org/files/sleep-edfx/1.0.0/sleep-cassette/`); 18 were
selected (one night per distinct subject number, avoiding any two nights
of the same subject) and downloaded via `curl`, all PSG files landing in
the expected 22–52 MB range (no truncated/corrupt files found by size
inspection). **No subjects excluded** — all 18 requested subjects have
complete PSG+Hypnogram pairs and load successfully (spot-verified on 3).

## 9.2 Physical sensing independence — VERIFIED

Real channel list read directly from a downloaded PSG file via `mne`:
`['EEG Fpz-Cz', 'EEG Pz-Oz', 'EOG horizontal', 'Resp oro-nasal', 'EMG submental', 'Temp rectal', 'Event marker']`,
sampling rate 100.0 Hz (shared clock, single file, single device). `EOG
horizontal` is recorded from electrodes placed near the eyes to capture
eye-movement potentials — a physically distinct electrode site and sensing
principle from the `EEG Fpz-Cz` scalp electrode pair; it is not
mathematically derived from the EEG channel. Both channels are always
present together in the source file at the same 100 Hz clock — no
resampling needed.

## 9.3 Split — FROZEN (seed 42, before any training)

Subject-wise, deterministic (same `subject_wise_split`-style shuffle
convention as PPG-DaLiA/PTT, seed=42), 12/3/3:

```
train (12): SC4001, SC4031, SC4051, SC4061, SC4071, SC4091, SC4101, SC4111, SC4121, SC4141, SC4161, SC4171
val   (3):  SC4021, SC4041, SC4151
test  (3):  SC4011, SC4081, SC4131
```

No sleep epoch from any subject appears in more than one partition (each
subject contributes only to the partition it is assigned to). Saved to
`ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json` before
training.

## 9.4 Task

5-class sleep-stage classification, standard AASM-era merge (`STAGE_NAMES`
already used by the existing single-channel baseline):
Wake / N1 / N2 / N3 (merged 3+4) / REM. No further class merging.
Real, verified label distribution on 3 spot-checked subjects: Wake is the
majority class (~70% of epochs) — Sleep-EDF cassette recordings include
substantial daytime/lights-on wake time, not just the sleep period. This
is disclosed now, before training, as the reason class-imbalance handling
(9.8) is necessary.

## 9.5 Epoching — unchanged, native

30-second epochs (`EPOCH_SECONDS = 30.0`), aligned to the real hypnogram
annotation boundaries exactly as the existing single-channel loader
already does — not changed for this experiment. Epochs falling in
unscored ("Sleep stage ?") or movement-artifact periods are dropped, never
guessed (same rule as the original loader).

## 9.6 Baseline and candidate — capacity-fairness applied from the start

**Baseline**: single-channel `EEG Fpz-Cz` only.
**Candidate**: `EEG Fpz-Cz` + `EOG horizontal` (2 channels).

Both use the **identical architecture**: one `Conv1DEncoder` (from
`backend/app/ml/models.py`, unmodified) with `in_channels` = 1 (baseline)
or 2 (candidate), followed by a `Linear(embedding_dim, 5)` classification
head — **no capacity-adding fusion module for the candidate** (unlike the
original, now-corrected PPG-DaLiA design). This directly applies the Day 7
capacity-confound lesson: a single shared encoder whose only difference is
first-layer input-channel count keeps the parameter-count gap small and
quantified (see below), rather than repeating the ModalityFusionTransformer
mistake.

## 9.7 Training parity — frozen before training

- Optimizer: AdamW, lr=0.001 (matches project convention).
- Epochs: 20 (matches project convention; no early stopping, matching the
  PPG-DaLiA-family convention rather than the PTT-family one — chosen for
  consistency with the majority of this project's prior experiments).
- Batch size: 64.
- Scheduler: none.
- Checkpoint-selection rule: final-epoch model (no early stopping, so no
  separate selection step - matches PPG-DaLiA convention).
- Augmentation: none.
- Seeds: 42, 43, 44, 45, 46 (identical set used throughout this project).
- Metric calculation: macro-F1 computed once per seed on the frozen held-out
  test set only, using scikit-learn's `f1_score(average="macro")`.
- Baseline and candidate use identical values for every item above.

## 9.8 Class imbalance — frozen policy

**Weighted cross-entropy loss, with class weights computed from TRAIN-split
label frequencies only** (`sklearn.utils.class_weight.compute_class_weight("balanced", ...)`
on the 12 training subjects' pooled epoch labels), applied identically to
baseline and candidate. Test-set class distribution is never used to tune
weights or the model. This is the frozen choice among the three options
listed in the master prompt (weighted CE chosen over a balanced sampler or
no weighting, because it requires no change to the data loader/batching
logic and is the most transparent to audit from a single stored weight
vector).

## 9.9 Seeds

42, 43, 44, 45, 46 — 5 seeds, matching project convention throughout.

## 9.10 Metrics

Primary: **macro-F1** (test set). Secondary: accuracy, balanced accuracy,
per-class F1, confusion matrix — all reported separately, never collapsed
into the primary metric.

## 9.11 Heterogeneity reporting (frozen requirement)

Must report, not just the aggregate: seed-to-seed variability (mean ±
sample SD, ddof=1, per the Day 7 stats-reporting fix), per-subject
macro-F1 (3 held-out test subjects), and per-class F1 (5 classes) for both
baseline and candidate. A positive aggregate must not erase subject- or
class-level heterogeneity — if the candidate improves overall but worsens
for a specific class (e.g. N1, typically the hardest class in this
dataset) or a specific subject, that must be stated in the headline
interpretation, not buried.

## Capacity disclosure (Section 11 requirement, addressed proactively)

Baseline (`in_channels=1`) and candidate (`in_channels=2`) share one
`Conv1DEncoder` class; the only architectural difference is the first
convolutional layer's input-channel count. Exact parameter counts will be
computed and reported before training results are inspected (both models
instantiate identically except for this one first-layer dimension) — this
will be reported as a small, quantified, first-layer-only difference,
analogous to Model A_cap's 0.77% residual, not a repeat of the original
~3.6x PPG-DaLiA confound.

## Outcome interpretation rules (frozen before results)

- **Candidate materially better** (macro-F1 improves beyond seed noise,
  consistent seed direction): positive target-specific marginal value for
  EOG on sleep-stage classification, under this dataset/protocol/model
  family. Not universal sensor necessity, not astronaut validation.
- **Near tie**: no strong evidence the added EOG channel materially helps
  this target under this frozen protocol.
- **Candidate worse**: negative marginal-value evidence, preserved and
  reported honestly, no post-hoc tuning to recover a positive result.
- **Heterogeneous**: if the aggregate improves but specific
  subjects/classes worsen, both the aggregate and the heterogeneity are
  reported together in the headline interpretation.

## Prohibited claims (regardless of outcome)

No claim of astronaut/microgravity sleep-monitoring validation, no claim
that EOG is necessary or sufficient for a final wearable, no numeric
comparison of this experiment's macro-F1 against any HR experiment's MAE
(different metrics, different tasks — cross-dataset/cross-metric ranking
is prohibited per `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`).
