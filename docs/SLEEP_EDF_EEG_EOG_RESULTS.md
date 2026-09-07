# Sleep-EDF EEG vs EEG+EOG — Results

Predeclaration: `docs/SLEEP_EDF_EEG_EOG_PREDECLARATION_DAY7.md` (frozen
before training). Artifact: `results/sleep_edf_eeg_eog_ablation.json`.
Reproducibility: `results/sleep_edf_eeg_eog_ablation_reproducibility.json`
(10/10 checkpoints reproduce exactly).

## Aggregate (5 seeds, sample SD ddof=1)

| Config | Params | Mean macro-F1 | Sample SD |
|---|---|---|---|
| Baseline (EEG only) | 8,197 | 0.7473 | 0.0244 |
| Candidate (EEG+EOG) | 8,309 | 0.7693 | 0.0132 |

Per-seed macro-F1 — baseline: 0.709 / 0.775 / 0.754 / 0.744 / 0.755.
Candidate: 0.761 / 0.772 / 0.791 / 0.762 / 0.760.

**Delta (candidate − baseline): +0.0220 ± 0.0228 (sample SD), 4/5 seeds
favor the candidate** (seed43 is a near-tie, −0.0032). The candidate also
shows **lower seed-to-seed variance** (0.0132 vs. 0.0244) — more stable
across independent initializations, in addition to the modest mean
improvement.

## Class-level heterogeneity (seed42 example, pattern consistent across seeds)

| Class | Baseline F1 | Candidate F1 | Δ |
|---|---|---|---|
| Wake | 0.967 | 0.982 | +0.015 |
| N1 | 0.304 | 0.450 | **+0.146** |
| N2 | 0.795 | 0.796 | +0.002 |
| N3 | 0.901 | 0.902 | +0.001 |
| REM | 0.577 | 0.674 | **+0.097** |

Every class improves or stays flat; **no class worsens**. The largest
gains are concentrated in **N1** (the hardest, rarest class in this
dataset) and **REM** — physiologically sensible, since REM sleep is
partly *defined* by rapid eye movements that EOG directly measures, and
N1 (the wake-to-sleep transition) is where eye-movement slowing is a
recognized scoring cue. This pattern is consistent with the sensor's real
physiological role, though this experiment does not "prove" the mechanism
— it only shows the class-level pattern is consistent with it.

Balanced accuracy is higher for the candidate in every one of the 5 seeds
(paired comparison), reinforcing the macro-F1 direction.

## Capacity disclosure

Baseline: 8,197 params. Candidate: 8,309 params (+112, 1.35% difference) —
a small, disclosed, first-conv-layer-only difference, not a repeat of the
PPG-DaLiA capacity confound (Model B/C there were 3.6x larger than Model
A). This result is not confounded by a large capacity gap.

## Interpretation (per the frozen outcome rules)

This falls closest to **"candidate materially better,"** with an
important qualification: the mean effect (+0.022) is comparable in
magnitude to its own seed-to-seed SD (0.023), so it should be reported as
a **modest, mostly-consistent (4/5 seeds)** positive effect, not an
overwhelming one — while noting the candidate's reduced variance and the
consistent, physiologically-sensible class-level pattern (N1/REM gains,
no class regressions) as corroborating, non-headline-metric evidence that
strengthens confidence beyond the macro-F1 mean/SD alone.

## Supported claim

Under this frozen protocol (18 real Sleep-EDF subjects, subject-disjoint
12/3/3 split, 5 training seeds, capacity-matched-to-within-1.35%
architecture), adding a synchronized EOG channel to a single-channel EEG
baseline produces a modest, mostly-consistent improvement in held-out
macro-F1 for 5-class sleep-stage classification (4/5 seeds favor the
candidate, mean +0.022, reduced variance), concentrated in the N1 and REM
classes and with no class showing regression.

## Unsupported claims

- No claim that EOG is necessary for sleep staging (baseline alone
  already reaches macro-F1 ≈0.75, a reasonably strong result).
- No claim of astronaut/microgravity sleep-monitoring validation.
- No numeric comparison of this macro-F1 result against any HR
  experiment's MAE (different metric, different task — prohibited by
  `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md`).
- No claim that this specific 1.35%-capacity-difference architecture is
  the only fair way to compare EEG vs. EEG+EOG — it is one defensible,
  predeclared choice.
- No claim about class-level *causal* mechanism beyond noting the pattern
  is physiologically consistent with EOG's known role.
