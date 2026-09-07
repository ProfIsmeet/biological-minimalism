# Sleep-EDF Shuffled-EOG Negative Control — Results

Predeclaration: `docs/SLEEP_EDF_SHUFFLED_EOG_PREDECLARATION.md` (frozen
before training). Artifact: `results/sleep_edf_eeg_eog_control_analysis.json`.
Reproducibility: `results/sleep_edf_shuffled_eog_control_reproducibility.json`
(5/5 checkpoints reproduce exactly).

## Aggregate (5 seeds, sample SD ddof=1)

| Model | Mean macro-F1 | Sample SD |
|---|---|---|
| A (EEG only) | 0.7473 | 0.0244 |
| B (EEG + aligned EOG) | 0.7693 | 0.0132 |
| **C (EEG + shuffled-within-subject EOG)** | **0.7420** | 0.0138 |

Per-seed C: 0.7454 / 0.7595 / 0.7343 / 0.7233 / 0.7476.

## Primary comparisons

| Comparison | Mean Δ | Seeds favoring 2nd term |
|---|---|---|
| A→B | +0.0220 ± 0.0228 | 4/5 favor B |
| A→C | −0.0052 ± 0.0241 | 1/5 favor C |
| **C→B** | **+0.0272 ± 0.0201** | **5/5 favor B** |

## Outcome classification (per the frozen predeclaration)

**Outcome 1**: B > C and C ≈ A. Confirmed directly: C's mean (0.7420) is
statistically indistinguishable from A's mean (0.7473) given their SDs,
and B beats C in every one of the 5 seeds (the cleanest, most consistent
directional result in this entire control). **Aligned EOG timing
contains useful task-specific information that does not survive
within-subject temporal shuffling.**

This is a stronger, cleaner result than the analogous PPG-DaLiA
shuffled-IMU control, where the shuffled condition (C) substantially beat
the unmodified baseline (A) — here, shuffling the EOG channel produces no
detectable benefit over EEG alone.

## Subject-level pattern (reinforcing, not just aggregate)

| Subject | A | B | C |
|---|---|---|---|
| SC4011 | 0.7335 | **0.7824** | 0.7111 |
| SC4081 | 0.7282 | 0.7362 | 0.7253 |
| SC4131 | 0.7634 | 0.7725 | 0.7671 |

SC4011 — the subject that showed the strongest aligned-EOG benefit in the
per-subject decomposition (`results/sleep_edf_per_subject_analysis.json`)
— is also the subject where shuffling drops performance the most (even
below the EEG-only baseline). The other two subjects (SC4081, SC4131)
show weak, closely-clustered A/B/C values — consistent with their
"MIXED" classification in the per-subject analysis. The story is
coherent: where the aligned-EOG benefit is real and strong, it
demonstrably depends on alignment; where the benefit was already weak,
shuffling doesn't change much because there was little to lose.

## Revised evidence strength

Upgraded from `preliminary` (Day 7) to **`replicated-with-control`**
(new category, added to the project's evidence-strength taxonomy this
sprint — see `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`): the positive
EOG effect is now supported by (a) 4/5 seed consistency in the primary
A→B comparison, (b) a clean, 5/5-consistent negative control showing the
effect depends on temporal alignment specifically, and (c) a coherent
subject-level pattern linking control behavior to where the primary
effect is strongest. Still limited to: one dataset, terrestrial
population, only 3 held-out test subjects.

## Revised claim

**Supported:** "Under the frozen protocol, adding a synchronized EOG
channel to a single-channel EEG baseline improves held-out macro-F1 for
5-class sleep-stage classification in 4/5 seeds (mean +0.022); this
benefit depends specifically on temporal alignment between EEG and EOG
epochs, since a capacity-identical shuffled-EOG control shows no
detectable benefit over EEG alone (mean Δ from baseline ≈ −0.005) and is
beaten by the aligned condition in 5/5 seeds. The effect is strongest for
one held-out subject (SC4011) and weak/mixed for the other two."

**Still unsupported:** EOG necessity, astronaut/microgravity validation,
any claim beyond this one dataset/population, any macro-F1-vs-MAE
numeric comparison against the HR experiments.
