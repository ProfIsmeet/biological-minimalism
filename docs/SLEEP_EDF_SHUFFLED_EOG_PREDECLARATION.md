# Sleep-EDF Shuffled-EOG Negative Control — Predeclaration (frozen before training)

**Research question:** Does the observed EEG+EOG macro-F1 improvement
depend on temporally aligned EOG information, or does a similar gain
survive when EOG-epoch correspondence with its true EEG epoch is
destroyed?

This mirrors the PPG-DaLiA shuffled-IMU negative control
(`shuffle_imu_within_subject`) applied to the Sleep-EDF EEG/EOG ablation.

## Shuffle method (frozen)

For each subject and each of its already-frozen partition assignments
(train/val/test — a subject belongs to exactly one partition, per the
existing frozen split), the EOG channel's epochs are randomly permuted
**among that subject's own epochs only**:

```
for subject in sorted(subjects_in_this_partition):
    eog_epochs = x[subject_mask, eog_channel_index, :]      # (n_epochs_subj, samples)
    permuted_order = rng.permutation(n_epochs_subj)          # same rng, advanced sequentially per subject
    x_shuffled[subject_mask, eog_channel_index, :] = eog_epochs[permuted_order]
    # EEG channel and labels for this subject are left untouched
```

- **Preserves the EOG signal distribution**: every real EOG epoch used in
  training/eval is still a genuine, real EOG recording from that same
  subject — none are fabricated, none come from a different subject.
- **Destroys EEG↔EOG temporal alignment**: the EOG epoch paired with a
  given EEG epoch (and its label) is now, with near-certainty, a
  different real epoch from the same recording.
- **Never crosses partitions**: shuffling happens independently within
  train, within val, and within test — no epoch from one partition is
  ever moved into another.
- **Never crosses subjects**: an epoch from one subject's EOG is never
  assigned to a different subject's EEG.
- **No label leakage**: the label array is never touched — it always
  corresponds to the real EEG epoch, exactly as in the aligned condition.
- **Deterministic per seed**: `np.random.default_rng(seed)`, advanced
  sequentially subject-by-subject in a fixed (sorted) subject order — the
  same seed always produces the same shuffle; different seeds (42–46,
  matching the training seed) produce different shuffles, exactly as
  `shuffle_imu_within_subject` was coupled to the training seed in the
  PPG-DaLiA design (Day 6 policy, reused here for consistency).
- **Test data was not used to design the shuffle** — the shuffle
  algorithm was written and frozen (this document) before any training or
  evaluation of the shuffled-EOG model.

## Architecture — capacity identical by construction

Model C uses the **exact same `SleepStageClassifier(in_channels=2)`
class** as Model B (the aligned EEG+EOG candidate) — same 8,309
parameters, verified identical (not just similar) since it is literally
the same class instantiated the same way. The only difference between B
and C is which EOG epochs are fed to the second input channel (aligned
vs. shuffled-within-subject-and-partition).

## Frozen training parity

Identical to the original Sleep-EDF ablation: AdamW, lr=0.001, batch=64,
epochs=20, no early stopping, train-only class weights, seeds 42–46,
macro-F1 primary metric, accuracy/balanced-accuracy/per-class-F1/
confusion-matrix secondary. Model C's training data uses the same
frozen 12/3/3 subject split as A and B.

## Comparisons (frozen)

A = EEG only, B = EEG + aligned EOG, C = EEG + shuffled EOG. Primary:
A→B, A→C, C→B (macro-F1). Same 5 seeds for all three.

## Interpretation rules (frozen before results)

- **Outcome 1** (B > C and C ≈ A): aligned EOG timing contains useful
  task-specific information beyond what a shuffled EOG channel provides.
- **Outcome 2** (B > C but C > A): some benefit survives shuffling
  (non-temporal EOG information, e.g. per-subject amplitude/variance
  statistics the model can still exploit even without correct timing);
  aligned timing adds additional value on top. **Not** described as "pure
  context" without further justification — that language is avoided per
  instruction.
- **Outcome 3** (B ≈ C > A): the observed gain may not depend strongly on
  temporal alignment specifically.
- **Outcome 4** (C ≥ B): current evidence does not support a
  synchronization-specific EOG benefit. This result would be preserved
  and reported exactly as found, not adjusted.

No outcome will trigger re-tuning of Model C after seeing its test
performance.

## Prohibited claims regardless of outcome

No claim of EOG necessity, no astronaut/microgravity validation, no
claim that this "proves" a causal mechanism, no numeric comparison
against any HR experiment's MAE.
