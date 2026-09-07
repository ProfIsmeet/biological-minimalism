# PPG-DaLiA Capacity-Matched Control — Results & Revised Interpretation

Predeclaration: `docs/PPG_DALIA_CAPACITY_CONTROL_PREDECLARATION.md` (frozen
before this run). Machine-readable artifact:
`results/ppg_dalia_capacity_control.json`. Does **not** overwrite
`results/ppg_dalia_imu_ablation.json` or
`results/ppg_dalia_imu_multiseed_replication.json`.

## Results (5 seeds, sample SD ddof=1)

| Model | Params | Mean MAE (bpm) | Sample SD |
|---|---|---|---|
| A (PPG-only, original) | 8,065 | 9.086 | 0.258 |
| **A_cap (PPG-only, capacity-matched)** | **28,865** | **7.813** | **0.423** |
| C (PPG+shuffled IMU, original) | 29,089 | 7.984 | 0.229 |
| B (PPG+synchronized IMU, original) | 29,089 | 7.208 | 0.175 |

Per-seed A_cap MAE: 7.558 / 7.839 / 7.555 / 7.574 / 8.539 bpm (seed 46 is a
mild outlier, still far below A, disclosed not excluded).

## Primary comparisons (sample SD ddof=1, positive = candidate better)

| Comparison | Mean Δ (bpm) | Seeds favoring 2nd term |
|---|---|---|
| A → A_cap | **1.273 ± 0.362** | 5/5 |
| A_cap → B | **0.605 ± 0.310** | 5/5 |
| A_cap → C | −0.171 ± 0.419 | 1/5 (C beats A_cap in only 1 of 5 seeds) |
| C → B | 0.776 ± 0.254 | 5/5 (unchanged - already capacity-matched originally) |

All three held-out subjects (S14, S2, S9) individually show the same
ordering: A_cap sits between A and B, materially closer to B than to A on
every subject.

## What this outcome is, per the frozen predeclaration

This is **Outcome 2**: "A_cap closes much of the gap to B. A substantial
fraction of previous A→B improvement was architecture/capacity-driven.
The IMU claim must be weakened accordingly." Predeclared before training;
no post-hoc tuning was applied to reach this classification.

## Revised decomposition of the original A→B gap (1.879 bpm total)

- **Capacity/architecture alone (A→A_cap), with zero real or shuffled
  IMU information**: 1.273 bpm ≈ **67.7%** of the original total gap.
- **Genuine IMU information on top of matched capacity (A_cap→B)**:
  0.605 bpm ≈ **32.2%** of the original total gap.

**A second, independently important finding**: A_cap (capacity-matched,
zero IMU information of any kind) performs approximately the same as, or
slightly better than, Model C (PPG+shuffled IMU) in 4 of 5 seeds. This
means the Day 6 interpretation "a substantial portion of the improvement
survived temporal shuffling, indicating synchronization-independent
context information" is **no longer well-supported as stated** — most of
what looked like "shuffled IMU carries context" was actually the same
capacity effect now isolated by A_cap, not genuine information carried by
the (shuffled) IMU channel itself.

**What remains solid and unchanged**: the C→B comparison was *already*
capacity-matched in the original design (C and B share the identical
architecture) — its result (0.776 ± 0.254 bpm, 5/5 seeds favor B) is
untouched by this control and remains the cleanest evidence in this whole
experiment family that **true temporal synchronization of IMU with PPG
provides a real, repeatable benefit beyond matched architecture capacity
and beyond a shuffled/context-only signal.**

## Revised claims

**What CAN still be claimed:** Under the frozen PPG-DaLiA protocol,
synchronized wrist IMU provides a real, 5-seed-consistent marginal
improvement in PPG-based HR estimation even after controlling for model
capacity (A_cap→B: 0.605±0.310 bpm, 5/5 seeds), and true synchronization
specifically (not just having an IMU-shaped input, shuffled or not) is
responsible for a real, 5-seed-consistent additional benefit over a
matched-capacity shuffled-IMU control (C→B: 0.776±0.254 bpm, 5/5 seeds).

**What CAN NO LONGER be claimed:**
- That the original ~1.88 bpm / ~20.6% "IMU benefit" reported in
  `results/ppg_dalia_imu_ablation.json` and the Day 6 multi-seed
  replication is attributable to IMU sensing information. **Most of it
  (≈68%) is now attributed to model capacity/architecture, not sensing.**
- That "a substantial portion of the improvement survived temporal
  shuffling" (the Day 6 shuffled-IMU interpretation) demonstrates
  synchronization-independent *information content* in the IMU channel —
  it is now better explained as the same capacity effect, not evidence
  that shuffled IMU carries real context.
- Any causal decomposition percentage as more than descriptive — this
  document's "67.7% / 32.2%" split is itself descriptive of one specific
  capacity-control design (A_cap), not a proven causal partition.

## Reproducibility

All 5 A_cap checkpoints saved (`ml/checkpoints/ppg_dalia_model_a_cap_seed*.pt`,
gitignored) with SHA256 recorded in `checkpoint_manifest` inside
`results/ppg_dalia_capacity_control.json`.
