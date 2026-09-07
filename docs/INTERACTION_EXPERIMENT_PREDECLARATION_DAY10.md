# Sleep-EDF EEG x EOG x Resp Interaction Experiment — Predeclaration (Day 10)

Frozen BEFORE training M_B or M_AB, and before viewing any performance
number for them. Selected via the formal feasibility audit in
`docs/INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md` (verdict:
`CLEAN_AND_FEASIBLE`, the only candidate marked clean out of three audited).

## Dataset

PhysioNet Sleep-EDFx sleep-cassette, same distribution already used by the
primary Sleep-EDF experiment. No new data acquisition.

## Target

5-class sleep stage (Wake/N1/N2/N3/REM), primary metric **macro-F1**,
identical to the primary and secondary Sleep-EDF experiments.

## Cohort / split

The **frozen primary split only** (`ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json`):
12 train / 3 validation / 3 test subjects. This experiment does **not**
touch the secondary holdout cohort (`ml/experiments/sleep_edf_secondary_holdout/cohort.json`)
- that cohort remains reserved for its own predeclared purpose and is not
reused here to avoid any appearance of cohort-shopping.

## Four configurations

| Config | Channels | Checkpoint source |
|---|---|---|
| M0 (baseline) | EEG Fpz-Cz | **Existing, frozen** - `ml/checkpoints/sleep_edf_baseline_eeg_only_seed{42-46}.pt`. Not retrained. |
| M_A (baseline + Candidate A) | EEG Fpz-Cz + EOG horizontal | **Existing, frozen** - `ml/checkpoints/sleep_edf_candidate_eeg_plus_eog_seed{42-46}.pt`. Not retrained. |
| M_B (baseline + Candidate B) | EEG Fpz-Cz + Resp oro-nasal | **New** - trained fresh for this experiment. |
| M_AB (baseline + A + B) | EEG Fpz-Cz + EOG horizontal + Resp oro-nasal | **New** - trained fresh for this experiment. |

Candidate A = EOG horizontal (already characterized: `replicated-with-control`,
prospectively holdout-supported). Candidate B = Resp oro-nasal (never used
by this project; not one of the official AASM/R&K sleep-staging scoring
channels, i.e. a genuinely independent information source relative to how
the ground-truth labels were originally produced).

## Architecture fairness

All four configurations use the **identical** `SleepStageClassifier` class
from `ml/train_sleep_edf_eeg_eog_ablation.py` (one shared `Conv1DEncoder`
+ `Linear(embedding_dim, 5)` head), differing **only** in `in_channels`
(1 for M0, 2 for M_A and M_B, 3 for M_AB). This is the exact convention
already used and audited for the primary EEG/EOG pair
(`capacity_confound_status: AVOIDED_BY_DESIGN`, residual parameter fraction
< 5%). No separate architecture family, no manual capacity tuning.
Parameter counts for all four configs will be recorded and asserted
consistent with this convention before any result is inspected.

## Seeds

42, 43, 44, 45, 46 - the project's frozen convention. All 5 seeds used
unconditionally for M_B and M_AB (M0/M_A already have all 5 seeds from
their original frozen runs). No seed is ever dropped after viewing results.

## Primary metric

macro-F1 (identical to the primary/secondary/control Sleep-EDF experiments).
Secondary: balanced accuracy, per-class F1, confusion matrix - identical to
the existing Sleep-EDF evaluation contract (`evaluate_full()`, reused
unmodified).

## Interaction definition (frozen before training)

For each seed s:

```
Benefit_A(s) = macro_F1(M_A, s) - macro_F1(M0, s)
Benefit_B(s) = macro_F1(M_B, s) - macro_F1(M0, s)
Benefit_AB(s) = macro_F1(M_AB, s) - macro_F1(M0, s)
Interaction(s) = Benefit_AB(s) - Benefit_A(s) - Benefit_B(s)
```

(Sign convention: macro-F1 is higher-is-better, so this is the direct
analogue of the MAE-based definition in the master sprint prompt, adapted
for a higher-is-better metric - no sign flip is needed since "benefit" is
already defined as candidate-minus-baseline in the improving direction.)

Interpretation (frozen, not to be adjusted after seeing results):
- **Interaction(s) > 0, consistently across seeds**: super-additive - EOG
  and Resp together help more than the sum of their individual effects.
- **Interaction(s) ≈ 0**: approximately additive - the two effects are
  largely independent.
- **Interaction(s) < 0, consistently across seeds**: sub-additive/redundant
  - the two channels partially duplicate each other's information.

This is a purely descriptive, statistical decomposition of measured
macro-F1 differences. It is **not** evidence of any physiological
mechanism, synergy, or redundancy at the signal-processing level, and must
never be described as such.

## Negative controls / capacity fairness safeguard

If, after training, `n_parameters(M_AB)` does not exactly equal
`n_parameters(M0) + (n_parameters(M_A) - n_parameters(M0)) + (n_parameters(M_B) - n_parameters(M0))`
under the shared-encoder-class convention (i.e., if the four configs are
not simple `in_channels` variants of one identical class), this experiment
is aborted and reported as deferred rather than interpreted - reusing the
Day-7 PPG-DaLiA capacity-confound lesson explicitly.

## Hard constraints (restated)

- Zero retraining of M0 or M_A - both loaded from existing frozen checkpoints.
- Zero use of the secondary holdout cohort.
- Zero seed selection after viewing results.
- Zero hyperparameter tuning beyond the frozen convention already used for
  every other Sleep-EDF config (20 epochs, batch 64, lr 0.001, AdamW,
  class-weighted cross-entropy, embedding_dim 32).
- Zero claim of physiological synergy/redundancy - only the descriptive
  statistical interaction term defined above.
