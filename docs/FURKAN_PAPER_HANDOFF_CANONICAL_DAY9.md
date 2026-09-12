# Furkan Paper-Support — Canonical State (Day 9)

Consolidates `FURKAN_PAPER_HANDOFF_DAY7.md`, `FURKAN_PAPER_SUPPORT_DAY8.md`, and
`FURKAN_PAPER_HANDOFF_DAY9.md` into one current paper-support state after the Day-9 canonical
integration. Every number below is artifact-backed (`results/claim_traceability.json`, 0 pending).

## What is writable NOW

### PPG-DaLiA (HR / IMU)
Capacity control is in: report the corrected interpretation. Original A→B ≈ 1.879 bpm (~20.6%
relative) is **capacity-confounded** (8,065 vs 28,865/29,089 params). ~68% of the A→B gap is
recovered by capacity/architecture alone (A_cap). A smaller capacity-controlled IMU benefit
remains: A_cap→B ~0.605 bpm and C→B ~0.776 bpm, both 5/5 seeds. **Do not** write "20.6%/23% pure
IMU", "1.88 bpm clean IMU", or a "59/41 causal split".

### PTT (HR / second PPG site)
Aggregate negative under the frozen protocol (one-site ~17.540 vs two-site ~19.003 MAE), 5/5
training seeds same aggregate direction, but strongly heterogeneous (2/4 subjects favor each way;
excluding s2 flips direction; s2 retained). Write it as bounded, heterogeneous, s2-sensitive
negative evidence — **not** a claim the second site is globally useless.

### Sleep-EDF (5-class / EOG) — now the strongest-supported case
- Primary (n=3): macro-F1 A 0.7473 → B 0.7693 (Δ ~0.022, 4/5 seeds); dominated by SC4011.
- Matched shuffled-EOG control: C 0.7420; C→B 5/5 seeds primary; A→C ≈ neutral.
- Prospective secondary holdout (n=8, frozen before eval, zero retraining): A 0.6530 → B 0.6858
  (A→B 5/5 seeds); C 0.6556; C→B 5/5; 6/8 subjects B>A, 7/8 B>C.
- Class-level (secondary): REM +0.150 (large), N3 −0.043 (regression, disclosed; precision effect).

**Canonical sentence for the paper:** *"Under a frozen capacity-matched protocol, aligned EOG
improved 5-class Sleep-EDF macro-F1 over EEG-only in the original primary test and again in a
prospectively frozen 8-subject secondary holdout. A capacity-identical shuffled-EOG control was
consistently worse than aligned EOG in both evaluations, supporting a role for temporally aligned
ocular information. The evidence remains single-dataset, terrestrial, and non-uniform across
subjects/classes."*

## What is future-only / must NOT be written
- Independent-dataset or cross-population replication.
- Pooled "n=11" sleep test set (report n=3 and n=8 separately).
- EOG necessity; final architecture contains EOG; population-wide EOG benefit.
- Astronaut / microgravity / spaceflight validation; trained Digital Twin.
- Cross-metric ranking (MAE vs macro-F1); a global/optimal sensor architecture.
- Formal Pareto (NOT_READY: no power/mass/BOM/interaction evidence).

## Provenance for methods section
Training env: Python 3.13.0, torch 2.6.0 CPU (`results/environment_manifest.json`). Checkpoints
externally archived and independently re-verified (GitHub Release `day8-checkpoint-archive-v1`,
SHA256 `5e0661a6…`, 50 checkpoints, 0 raw datasets). Evidence strength: replicated-with-control +
prospective_secondary_holdout_supported.
