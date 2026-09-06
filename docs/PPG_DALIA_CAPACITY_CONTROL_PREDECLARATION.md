# PPG-DaLiA Capacity-Matched Control — Predeclaration (frozen before training)

**Master review finding being addressed (Finding A3, HIGH):** Model A
(PPG-only, 8,065 parameters) and Model B/C (PPG+IMU, 29,089 parameters,
3.61x larger) are not capacity-matched. Verified directly against the
actual model code before writing this document — the finding is real, not
assumed. This means the original A→B comparison conflates two variables:
(1) sensing information (IMU present/absent) and (2) model
architecture/capacity (single encoder vs. two-encoder+fusion-transformer).
Only C→B (both use the full two-encoder+fusion architecture) was already
capacity-matched.

## 1. Architectural rationale

`Model A_cap`: the **exact same architecture family as Model B/C**
(two `Conv1DEncoder` instances + the unmodified `ModalityFusionTransformer`
+ `Linear` head), but **both encoder inputs receive the same real PPG
window** — no IMU, no new information, no synthetic/zero-padded input.
The second branch is an independently-initialized `Conv1DEncoder` over the
identical PPG signal (a redundant, genuinely-trained encoding of the same
information), fused via the same cross-attention transformer used by
Model B/C.

This is not "padding with dead parameters": both branches receive real
gradient signal from real data every training step (verified: both
encoders process real, non-zero PPG windows; no `modality_mask` masking
is used, which would have left the second encoder's weights untrained —
that design was explicitly considered and rejected for exactly this
reason).

The goal is to isolate **architecture/capacity** as the explanatory
variable while holding **input information content constant at
"PPG only"** — the complement of the original C→B comparison, which held
input information non-identical (shuffled vs. real IMU) while holding
architecture constant.

## 2. Exact parameter count

- Model A (original, unchanged): **8,065** parameters.
- Model B / Model C (original, unchanged): **29,089** parameters each.
- **Model A_cap: 28,865** parameters.
- Residual difference from Model B/C: **224 parameters (0.77%)**, arising
  entirely from the first convolutional layer's input-channel count
  (second branch: 1 channel for duplicated PPG vs. 3 channels for real
  IMU in Model B/C — `Conv1d(in_channels, 16, kernel_size=7)` weight count
  scales with `in_channels`: 16×1×7=112 vs. 16×3×7=336, a 224-weight
  difference). **This residual is judged scientifically immaterial**:
  0.77% of total capacity is far smaller than the ~261% capacity gap
  (29,089 vs. 8,065) this control is designed to close, and it affects
  only the first layer's input projection, not depth, width, or the
  fusion mechanism.

## 3. How capacity comparability is defined here

Total learnable parameter count, with the additional (harder) requirement
that every parameter be reachable by gradient descent under normal
training (no masked/frozen/dead branches) — verified by construction
(both encoders always receive real non-zero input, both always participate
in the fusion attention with `modality_mask=all True`).

## 4. What remains different by necessity

- The 224-parameter residual (§2), disclosed and judged immaterial.
- A_cap's second branch sees a *duplicate* of the same PPG signal, not an
  independent physical measurement — by design, since the entire point is
  to test whether architecture alone (without new information) can
  produce a benefit similar to Model B's.

## 5. Frozen preprocessing

Identical to the original experiment: per-window PPG z-score (same
`zscore_ppg_window`), same cached windows, same HR target normalization
(train-split-only mean/std). A_cap's second "modality" is simply the same
z-scored PPG tensor passed to both encoder inputs — no separate
normalization is invented for it.

## 6. Frozen train/val/test split

Unchanged: `ml/experiments/ppg_dalia_imu_ablation/subject_split.json`
(train=10, val=2, test=3 subjects: S14, S2, S9), loaded, never recomputed
— same file used by the Day 6 multi-seed replication.

## 7. Frozen seeds

42, 43, 44, 45, 46 — the same five seeds used for the Day 6 replication,
for direct paired comparability (A, A_cap, B, C all share the same seed
set).

## 8. Primary / secondary metric

Primary: MAE (bpm), held-out test set. Secondary: RMSE (bpm). Same
train-only HR normalization as the original experiment. No new metric is
introduced for this control.

## 9. Training parity

Identical hyperparameters to the original/replication experiments:
AdamW, MSELoss on normalized HR, lr=0.001, batch_size=64, epochs=20,
embedding_dim=32, no early stopping (matches the original PPG-DaLiA
convention — fixed 20 epochs, final-epoch model used for test evaluation,
NOT the PTT-style early-stopping convention). `torch.set_num_threads(4)`
(the Day 6 infrastructure fix, not a scientific parameter).

## 10. Interpretation rules (frozen BEFORE seeing any A_cap result)

Primary comparison set: **A vs. A_cap**, **A_cap vs. B**, **A_cap vs. C**,
**C vs. B** (already established). All four outcome categories below are
predeclared as acceptable, in either direction:

- **Outcome 1 — A_cap ≈ A, A_cap materially worse than B**: evidence that
  the original B advantage is NOT explained by capacity alone becomes
  substantially stronger (the "clean IMU-information" interpretation is
  reinforced).
- **Outcome 2 — A_cap closes much of the A→B gap**: a substantial fraction
  of the original A→B improvement was architecture/capacity-driven, not
  IMU-information-driven. The IMU marginal-value claim must be weakened
  accordingly, in proportion to how much of the gap A_cap closes.
- **Outcome 3 — A_cap ≈ B**: current evidence does NOT establish a
  meaningful IMU marginal-value benefit beyond architecture-capacity/
  context effects. This would be a materially revised (weakened)
  conclusion relative to the original single/multi-seed reports.
- **Outcome 4 — A_cap outperforms B**: the original sensor-value
  conclusion is overturned or materially revised. Scientifically
  acceptable; would not be suppressed or retrained away.

**No outcome will trigger retraining, re-tuning, or architecture changes
to A_cap.** Whatever the five seeds produce is reported as-is.

## 11. Claims that remain prohibited regardless of result

- No claim that this control alone proves synchronization is or is not
  causally responsible for any remaining gap (that question is addressed,
  separately and already capacity-matched, by the existing C→B
  comparison).
- No claim of astronaut/microgravity relevance.
- No claim that this closes the interaction-effects/combinatorial-
  optimality question (see the separate interaction-limitation
  documentation).
- No re-labeling of the original A/B/C experiment's results — this is a
  **supplemental, separately-versioned artifact**
  (`results/ppg_dalia_capacity_control.json`), not an overwrite of
  `results/ppg_dalia_imu_ablation.json` or
  `results/ppg_dalia_imu_multiseed_replication.json`.
- No claim that 0.77% residual capacity difference is exactly zero — it
  is disclosed, not hidden, even though judged immaterial.
